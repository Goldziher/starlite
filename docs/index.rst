:layout: landing
:description: Litestar is a powerful, flexible, highly performant, and opinionated ASGI framework.

.. container::
    :name: home-head

    .. image:: https://raw.githubusercontent.com/litestar-org/branding/main/assets/Branding%20-%20SVG%20-%20Transparent/Badge%20-%20Blue%20and%20Yellow.svg
        :alt: Litestar Framework
        :width: 400
        :height: 400

    .. container::

        .. raw:: html

            <h1>Litestar</h1>

        .. container:: badges
           :name: badges

            .. image:: https://img.shields.io/github/actions/workflow/status/litestar-org/litestar/publish.yml?labelColor=202235&logo=github&logoColor=edb641
               :alt: GitHub Actions Latest Release Workflow Status

            .. image:: https://img.shields.io/github/actions/workflow/status/litestar-org/litestar/ci.yml?labelColor=202235&logo=github&logoColor=edb641
               :alt: GitHub Actions CI Workflow Status

            .. image:: https://img.shields.io/github/actions/workflow/status/litestar-org/litestar/docs.yml?labelColor=202235&logo=github&logoColor=edb641
               :alt: GitHub Actions Docs Build Workflow Status

            .. image:: https://img.shields.io/codecov/c/github/litestar-org/litestar?labelColor=202235&logo=codecov&logoColor=edb641
               :alt: Coverage

            .. image:: https://img.shields.io/pypi/v/litestar?labelColor=202235&color=edb641&logo=python&logoColor=edb641
               :alt: PyPI Version

            .. image:: https://img.shields.io/github/all-contributors/litestar-org/litestar?labelColor=202235&color=edb641&logoColor=edb641
               :alt: Contributor Count

            .. image:: https://img.shields.io/pypi/dm/litestar?logo=python&label=litestar%20downloads&labelColor=202235&color=edb641&logoColor=edb641
               :alt: PyPI Downloads

            .. image:: https://img.shields.io/pypi/pyversions/litestar?labelColor=202235&color=edb641&logo=python&logoColor=edb641
               :alt: Supported Python Versions

.. rst-class:: lead

   The Litestar framework supports :doc:`/usage/plugins/index`, ships with
   :doc:`dependency injection </usage/dependency-injection>`, :doc:`security primitives </usage/security/index>`,
   :doc:`OpenAPI schema generation </usage/openapi/index>`, `MessagePack <https://msgpack.org/>`_,
   :doc:`middlewares </usage/middleware/index>`, a great :doc:`CLI </usage/cli>` experience, and much more.

.. container:: buttons

    :doc:`Get Started <getting-started>`
    `Usage Docs <usage>`_
    `API Docs <reference>`_
    `Blog <https://blog.litestar.dev>`_

.. grid:: 1 1 2 3
    :padding: 0
    :gutter: 2

    .. grid-item-card:: :octicon:`repo` Tutorials
      :link: tutorials/index
      :link-type: doc

      Step-by-step guides addressing common use cases and scenarios for Litestar

    .. grid-item-card:: :octicon:`light-bulb` Topics
      :link: topics/index
      :link-type: doc

      Articles discussing technical concepts, design philosophy, and strategic decisions.

    .. grid-item-card:: :octicon:`versions` Changelog
      :link: release-notes/changelog
      :link-type: doc

      The latest updates and enhancements to the Litestar framework.

    .. grid-item-card:: :octicon:`comment-discussion` Discussions
      :link: https://github.com/litestar-org/litestar/discussions

      Join discussions, pose questions, or share insights.

    .. grid-item-card:: :octicon:`issue-opened` Issues
      :link: https://github.com/litestar-org/litestar/issues

      Report issues or suggest new features.

    .. grid-item-card:: :octicon:`beaker` Contributing
      :link: contribution-guide
      :link-type: doc

      Contribute to Litestar's growth with code, docs, and more.

Sponsors
--------

.. rst-class:: lead

   Litestar is a community-driven, open-source initiative that thrives on the generous contributions of our sponsors,
   enabling us to pursue innovative developments and continue our mission to provide exceptional tools and resources
   to our users.


A huge thank you to our current sponsors:

.. container::
   :name: sponsors-section

   .. grid:: 3
      :class-row: surface
      :padding: 0
      :gutter: 2

      .. grid-item-card::
         :link: https://github.com/scalar/scalar

         .. image:: https://raw.githubusercontent.com/litestar-org/branding/main/assets/sponsors/scalar.svg
            :alt: Scalar.com
            :class: sponsor

         `Scalar.com <https://github.com/scalar/scalar>`_

      .. grid-item-card::
         :link: https://telemetrysports.com/

         .. image:: https://raw.githubusercontent.com/litestar-org/branding/main/assets/sponsors/telemetry-sports/unofficial-telemetry-whitebg.svg
            :alt: Telemetry Sports
            :class: sponsor

         `Telemetry Sports <https://telemetrysports.com/>`_

      .. grid-item-card::
         :link: https://www.stok.kr/

         .. image:: https://avatars.githubusercontent.com/u/144093421
            :alt: Stok
            :class: sponsor

         `Stok <https://www.stok.kr/>`_

We invite organizations and individuals to join our sponsorship program.
By becoming a sponsor on platforms like `Polar <sponsor-polar_>`_, `GitHub <sponsor-github_>`_
and `Open Collective <sponsor-oc_>`_, you can play a pivotal role in our project's growth.

On top of regular sponsorship, we engage in pledge-based sponsorship opportunities through `Polar <sponsor-polar_>`_,
where you can pledge an amount towards an issue or feature you would like to see implemented.


.. _sponsor-github: https://github.com/sponsors/litestar-org
.. _sponsor-oc: https://opencollective.com/litestar
.. _sponsor-polar: https://polar.sh/litestar-org

.. toctree::
    :titlesonly:
    :caption: Documentation
    :hidden:

    getting-started
    usage/index
    reference/index
    benchmarks

.. toctree::
    :titlesonly:
    :caption: Guides
    :hidden:

    migration/index
    topics/index
    tutorials/index

.. toctree::
    :titlesonly:
    :caption: Contributing
    :hidden:

    contribution-guide
    Available Issues <https://github.com/search?q=user%3Alitestar-org+state%3Aopen+label%3A%22good+first+issue%22+++no%3Aassignee+&type=issues=>
    Code of Conduct <https://github.com/litestar-org/.github?tab=coc-ov-file#readme>
