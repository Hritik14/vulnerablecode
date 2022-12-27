===============
VulnerableCode
===============

|Build Status| |Code License| |Data License| |Python 3.8+| |stability-wip| |Gitter chat|


.. |Build Status| image:: https://github.com/nexB/vulnerablecode/actions/workflows/main.yml/badge.svg?branch=main
   :target: https://github.com/nexB/vulnerablecode/actions?query=workflow%3ACI
.. |Code License| image:: https://img.shields.io/badge/Code%20License-Apache--2.0-green.svg
   :target: https://opensource.org/licenses/Apache-2.0
.. |Data License| image:: https://img.shields.io/badge/Data%20License-CC--BY--SA--4.0-green.svg
   :target: https://creativecommons.org/licenses/by-sa/4.0/legalcode 
.. |Python 3.8+| image:: https://img.shields.io/badge/python-3.8+-green.svg
   :target: https://www.python.org/downloads/release/python-380/
.. |stability-wip| image:: https://img.shields.io/badge/stability-work_in_progress-lightgrey.svg
.. |Gitter chat| image:: https://badges.gitter.im/gitterHQ/gitter.png
   :target: https://gitter.im/aboutcode-org/vulnerablecode


VulnerableCode is a free and open database of open source software package
vulnerabilities **because open source software vulnerabilities data and tools
should be free and open source themselves**:

Read more about VulnerableCode https://vulnerablecode.readthedocs.org/

Hritik's Fork
==============

.. code-block::

    git clone git@github.com:Hritik14/vulnerablecode.git
    cd vulnerablecode
    make dev
    . venv/bin/activate
    pip install pylint pylint_django
    git config --global merge.ours.driver true
    ...
    git remote set-url origin git@github.com:nexB/vulnerablecode.git
    git remote add fork git@github.com:Hritik14/vulnerablecode.git
    git branch forkmain
    git fetch fork
    git branch forkmain --set-upstream-to fork/main
    git branch main --set-upstream-to origin/main
    git pull origin main --rebase
    git checkout forkmain
    git merge main
    git push fork forkmain:main
    git checkout main
    git restore --source=fork/main .pylintrc

See: .pylintrc
