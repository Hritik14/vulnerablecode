# Copyright (c) nexB Inc. and others. All rights reserved.
# http://nexb.com and https://github.com/nexB/vulnerablecode/
# The VulnerableCode software is licensed under the Apache License version 2.0.
# Data generated with VulnerableCode require an acknowledgment.
#
# You may not use this software except in compliance with the License.
# You may obtain a copy of the License at: http://apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#
# When you publish or redistribute any data created with VulnerableCode or any VulnerableCode
# derivative work, you must accompany this data with the following acknowledgment:
#
#  Generated with VulnerableCode and provided on an "AS IS" BASIS, WITHOUT WARRANTIES
#  OR CONDITIONS OF ANY KIND, either express or implied. No content created from
#  VulnerableCode should be considered or used as legal advice. Consult an Attorney
#  for any legal advice.
#  VulnerableCode is a free software tool from nexB Inc. and others.
#  Visit https://github.com/nexB/vulnerablecode/ for support and download.

import dataclasses
import datetime
from typing import Iterable

import requests
from bs4 import BeautifulSoup
from packageurl import PackageURL
from univers.version_range import NginxVersionRange
from univers.versions import SemverVersion

from vulnerabilities.data_source import AdvisoryData
from vulnerabilities.data_source import AffectedPackage
from vulnerabilities.data_source import DataSource
from vulnerabilities.data_source import DataSourceConfiguration
from vulnerabilities.data_source import Reference
from vulnerabilities.data_source import VulnerabilitySeverity
from vulnerabilities.helpers import nearest_patched_package
from vulnerabilities.package_managers import GitHubTagsAPI
from vulnerabilities.package_managers import Version
from vulnerabilities.severity_systems import scoring_systems


@dataclasses.dataclass
class NginxDataSourceConfiguration(DataSourceConfiguration):
    etags: dict


class NginxDataSource(DataSource):
    CONFIG_CLASS = NginxDataSourceConfiguration

    url = "http://nginx.org/en/security_advisories.html"

    def advisory_data(self) -> Iterable[AdvisoryData]:
        data = requests.get(self.url).content
        soup = BeautifulSoup(data, features="lxml")
        vuln_list = soup.select("li p")
        for vuln_info in vuln_list:
            yield to_advisory_data(**parse_advisory_data_from_paragraph(vuln_info))


def to_advisory_data(
    cve, summary, advisory_severity, not_vulnerable, vulnerable, references
) -> AdvisoryData:
    """
    Return AdvisoryData formed by given parameters
    An advisory paragraph, without html markup, looks like:

    1-byte memory overwrite in resolver
    Severity: medium
    Advisory
    CVE-2021-23017
    Not vulnerable: 1.21.0+, 1.20.1+
    Vulnerable: 0.6.18-1.20.0
    The patch  pgp
    """

    qualifiers = {}

    affected_version_range = vulnerable.partition(":")[2]
    if "nginx/Windows" in affected_version_range:
        qualifiers["os"] = "windows"
        affected_version_range = affected_version_range.replace("nginx/Windows", "")
    affected_version_range = NginxVersionRange.from_native(affected_version_range)

    affected_packages = []
    _, _, fixed_versions = not_vulnerable.partition(":")
    for fixed_version in fixed_versions.split(","):
        fixed_version = fixed_version.rstrip("+")

        # TODO: Mail nginx for this anomaly
        if "none" in fixed_version:
            # FIXME: This breaks because https://github.com/nexB/univers/issues/10
            break
            # affected_packages.append(
            #     AffectedPackage(
            #         package=PackageURL(type="generic", name="nginx", qualifiers=qualifiers),
            #         affected_version_range=affected_version_range,
            #     )
            # )
            # break

        fixed_version = SemverVersion(fixed_version)
        purl = PackageURL(type="generic", name="nginx", qualifiers=qualifiers)
        affected_packages.append(
            AffectedPackage(
                package=purl,
                affected_version_range=affected_version_range,
                fixed_version=fixed_version,
            )
        )

    return AdvisoryData(
        vulnerability_id=cve,
        summary=summary,
        affected_packages=affected_packages,
        references=references,
        date_published=datetime.datetime.now(tz=datetime.timezone.utc),
    )


def parse_advisory_data_from_paragraph(vuln_info):
    """
    Return (summary, advisory_severity, not_vulnerable, vulnerable, references)
    from bs4 paragraph

    For example:
    >>> paragraph = '<p>1-byte memory overwrite in resolver<br/>Severity: medium<br/><a href="http://mailman.nginx.org/pipermail/nginx-announce/2021/000300.html">Advisory</a><br/><a href="http://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-23017">CVE-2021-23017</a><br/>Not vulnerable: 1.21.0+, 1.20.1+<br/>Vulnerable: 0.6.18-1.20.0<br/><a href="/download/patch.2021.resolver.txt">The patch</a>  <a href="/download/patch.2021.resolver.txt.asc">pgp</a></p>'
    >>> vuln_info = BeautifulSoup(paragraph).p
    >>> parse_advisory_data_from_paragraph(vuln_info)
    ('CVE-2021-23017', '1-byte memory overwrite in resolver', 'Severity: medium', 'Not vulnerable: 1.21.0+, 1.20.1+', 'Vulnerable: 0.6.18-1.20.0', [Reference(reference_id='', url='http://mailman.nginx.org/pipermail/nginx-announce/2021/000300.html', severities=[]), Reference(reference_id='CVE-2021-23017', url='http://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-23017', severities=[VulnerabilitySeverity(system=ScoringSystem(identifier='generic_textual', name='Generic textual severity rating', url='', notes='Severity for unknown scoring systems. Contains generic textual values like High, Low etc'), value='Severity: medium')]), Reference(reference_id='', url='https://nginx.org/download/patch.2021.resolver.txt', severities=[]), Reference(reference_id='', url='https://nginx.org/download/patch.2021.resolver.txt.asc', severities=[])])
    """
    cve = summary = advisory_severity = not_vulnerable = vulnerable = None
    references = []
    for index, child in enumerate(vuln_info.children):
        if index == 0:
            summary = child
            continue

        if "Severity" in child:
            advisory_severity = child
            continue

        #  hasattr(child, "attrs") == False for bs4.element.NavigableString
        if hasattr(child, "attrs") and child.attrs.get("href"):
            link = child.attrs["href"]
            # Take care of relative urls
            link = requests.compat.urljoin("https://nginx.org", link)
            if "cve.mitre.org" in link:
                cve = child.text
                references.append(
                    Reference(
                        reference_id=cve,
                        url=link,
                    )
                )
            elif "http://mailman.nginx.org" in link:
                references.append(
                    Reference(
                        url=link,
                        severities=[
                            VulnerabilitySeverity(
                                system=scoring_systems["generic_textual"],
                                value=advisory_severity,
                            )
                        ],
                    )
                )
            else:
                references.append(Reference(url=link))
            continue

        if "Not vulnerable" in child:
            not_vulnerable = child
            continue

        if "Vulnerable" in child:
            vulnerable = child
            continue

    return {
        "cve": cve,
        "summary": summary,
        "advisory_severity": advisory_severity,
        "not_vulnerable": not_vulnerable,
        "vulnerable": vulnerable,
        "references": references,
    }
