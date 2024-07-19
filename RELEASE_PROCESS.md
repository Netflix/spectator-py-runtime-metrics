## Automated Relase Process

See [Publishing package distribution releases using GitHub Actions CI/CD workflows](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/) for more details.

1. Bump the version number in [setup.py](./setup.py).

1. Tag the repo and write release notes. The goal is for the [releases] page to be readable.

    1. Clone the upstream project.

    1. Create a new tag.

            git tag -a v0.1.X

    1. Push the tag to the origin. This will trigger the release action, which will build and publish to PyPI.

            git push origin v0.1.X

    1. Project > Releases > Tags > Select Tag > Create Release

            Primary changes:

            - #<PR number>, <short description>.

            A comprehensive list of changes can be found in the commit log: https://github.com/Netflix/spectator-py-runtime-metrics/compare/v0.1.<N-1>...v0.1.<N>

## Manual Release Process

1. Pre-Requisites.

    1. Install packaging tools.

            pip3 install setuptools wheel twine

    1. Configure [PyPI] username.

            cat >~/.pypirc <<EOF
            [distutils]
            index-servers = pypi

            [pypi]
            username: $PYPI_USERNAME
            EOF

1. Bump the version number in [setup.py](./setup.py).

1. Tag the repo and write release notes. The goal is for the [releases] page to be readable.

    1. Clone the upstream project.

    1. Create a new tag.

            git tag -a v0.1.X

    1. Push the tags to the origin.

            git push origin v0.1.X

    1. Project > Releases > Tags > Select Tag > Create Release

            Primary changes:

            - #<PR number>, <short description>.

            A comprehensive list of changes can be found in the commit log: https://github.com/Netflix/spectator-py-runtime-metrics/compare/v0.1.<N-1>...v0.1.<N>

1. On your local machine, checkout the tag and run the following command, which will build the
package and upload it to [PyPI].

        rm -rf dist
        git checkout $TAG
        python3 setup.py sdist bdist_wheel
        twine check dist/*
        twine upload dist/*

[PyPI]: https://pypi.org/project/netflix-spectator-py-runtime-metrics/
[releases]: https://github.com/Netflix/spectator-py-runtime-metrics/releases
