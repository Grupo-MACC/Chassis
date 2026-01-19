"""
setup.py

Este setup.py deja de hardcodear la versión.
La versión se obtiene de tags Git mediante setuptools_scm (configurado en pyproject.toml).

Nota:
    Con pyproject.toml presente, lo normal es construir con:
        python -m build
    y no con setup.py directamente.
"""

from setuptools import setup, find_packages


setup(
    name="microservice_chassis_grupo2_cc_prod",
    #version=find_packages
    packages=find_packages(),
    use_scm_version=True,  # <-- clave: versión por tags
    description="A reusable library for microservices",
    url="https://github.com/Grupo-MACC/Chassis",
    author="Grupo 2",
    author_email="",
    install_requires=[]
)
