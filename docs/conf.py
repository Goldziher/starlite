from __future__ import annotations

import importlib.metadata
import os
import re
import warnings
from functools import partial
from typing import Any

from sphinx.addnodes import document
from sphinx.application import Sphinx
from sqlalchemy.exc import SAWarning

warnings.filterwarnings("ignore", category=SAWarning)

__all__ = ["setup", "update_html_context"]

PY_CLASS = "py:class"
PY_RE = r"py:.*"
PY_METH = "py:meth"
PY_ATTR = "py:attr"
PY_OBJ = "py:obj"
PY_FUNC = "py:func"

project = "Litestar"
copyright = "2023, Litestar-Org"
author = "Litestar-Org"
release = os.getenv("_LITESTAR_DOCS_BUILD_VERSION", importlib.metadata.version("litestar").rsplit(".")[0])

extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_design",
    "auto_pytabs.sphinx_ext",
    "tools.sphinx_ext",
    "sphinx_copybutton",
    "sphinxcontrib.mermaid",
    "sphinx_click",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "msgspec": ("https://jcristharif.com/msgspec/", None),
    "anyio": ("https://anyio.readthedocs.io/en/stable/", None),
    "multidict": ("https://multidict.aio-libs.org/en/stable/", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
    "click": ("https://click.palletsprojects.com/en/8.1.x/", None),
    "redis": ("https://redis-py.readthedocs.io/en/stable/", None),
    "picologging": ("https://microsoft.github.io/picologging", None),
    "structlog": ("https://www.structlog.org/en/stable/", None),
    "tortoise": ("https://tortoise.github.io/", None),
    "piccolo": ("https://piccolo-orm.readthedocs.io/en/latest", None),
    "opentelemetry": ("https://opentelemetry-python.readthedocs.io/en/latest/", None),
    "advanced-alchemy": ("https://docs.advanced-alchemy.jolt.rs/latest/", None),
    "jinja2": ("https://jinja.palletsprojects.com/en/latest/", None),
    "trio": ("https://trio.readthedocs.io/en/stable/", None),
}

napoleon_google_docstring = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_attr_annotations = True

autoclass_content = "class"
autodoc_class_signature = "separated"
autodoc_default_options = {"special-members": "__init__", "show-inheritance": True, "members": True}
autodoc_member_order = "bysource"
autodoc_typehints_format = "short"

nitpicky = True
nitpick_ignore = [
    # external library / undocumented external
    (PY_CLASS, "BaseModel"),
    (PY_CLASS, "ExternalType"),
    (PY_CLASS, "TypeEngine"),
    (PY_CLASS, "UserDefinedType"),
    (PY_CLASS, "_RegistryType"),
    (PY_CLASS, "_orm.Mapper"),
    (PY_CLASS, "_orm.registry"),
    (PY_CLASS, "_schema.MetaData"),
    (PY_CLASS, "_schema.Table"),
    (PY_CLASS, "_types.TypeDecorator"),
    (PY_CLASS, "abc.Collection"),
    (PY_CLASS, "advanced_alchemy.utils.dataclass.Empty"),
    (PY_CLASS, "jinja2.environment.Environment"),
    (PY_CLASS, "pydantic.BaseModel"),
    (PY_CLASS, "pydantic.generics.GenericModel"),
    (PY_CLASS, "pydantic.main.BaseModel"),
    (PY_CLASS, "redis.asyncio.Redis"),
    (PY_CLASS, "sqlalchemy.dialects.postgresql.named_types.ENUM"),
    (PY_CLASS, "sqlalchemy.orm.decl_api.DeclarativeMeta"),
    (PY_CLASS, "sqlalchemy.sql.sqltypes.TupleType"),
    (PY_METH, "_types.TypeDecorator.process_bind_param"),
    (PY_METH, "_types.TypeDecorator.process_result_value"),
    (PY_METH, "litestar.typing.ParsedType.is_subclass_of"),
    (PY_METH, "type_engine"),
    # type vars and aliases / intentionally undocumented
    (PY_CLASS, "AnyIOBackend"),
    (PY_CLASS, "BaseSessionBackendT"),
    (PY_CLASS, "C"),
    (PY_CLASS, "CollectionT"),
    (PY_CLASS, "ControllerRouterHandler"),
    (PY_CLASS, "EmptyType"),
    (PY_CLASS, "ModelT"),
    (PY_CLASS, "PathParameterDefinition"),
    (PY_CLASS, "RouteHandlerType"),
    (PY_CLASS, "SelectT"),
    (PY_CLASS, "T"),
    (PY_OBJ, "litestar.security.base.AuthType"),
    # investigate
    (PY_CLASS, "Environment"),
    (PY_CLASS, "P"),
    (PY_CLASS, "pydantic_v1.BaseModel"),
    (PY_CLASS, "pydantic_v2.BaseModel"),
    (PY_CLASS, "advanced_alchemy.config.types.Empty"),
    (PY_OBJ, "litestar.template.base.TemplateType_co"),
    (PY_OBJ, "litestar.template.base.ContextType_co"),
    (PY_CLASS, "litestar.template.base.TemplateType_co"),
    (PY_CLASS, "litestar.template.base.ContextType_co"),
    (PY_CLASS, "litestar.template.base.R"),
    (PY_ATTR, "litestar.openapi.controller.OpenAPIController.swagger_ui_init_oauth"),
    # intentionally undocumented
    (PY_CLASS, "BacklogStrategy"),
    (PY_CLASS, "ExceptionT"),
    (PY_CLASS, "NoneType"),
    (PY_CLASS, "litestar._openapi.schema_generation.schema.SchemaCreator"),
    (PY_CLASS, "litestar._signature.model.SignatureModel"),
    (PY_CLASS, "litestar.contrib.sqlalchemy.plugins.init.config.compat._CreateEngineMixin"),
    (PY_CLASS, "litestar.utils.signature.ParsedSignature"),
    (PY_CLASS, "litestar.utils.sync.AsyncCallable"),
    # types in changelog that no longer exist
    (PY_ATTR, "litestar.dto.factory.DTOConfig.underscore_fields_private"),
    (PY_CLASS, "anyio.abc.BlockingPortal"),
    (PY_CLASS, "litestar.contrib.msgspec.MsgspecDTO"),
    (PY_CLASS, "litestar.contrib.repository.filters.NotInCollectionFilter"),
    (PY_CLASS, "litestar.contrib.repository.filters.NotInSearchFilter"),
    (PY_CLASS, "litestar.contrib.repository.filters.OnBeforeAfter"),
    (PY_CLASS, "litestar.contrib.repository.filters.OrderBy"),
    (PY_CLASS, "litestar.contrib.repository.filters.SearchFilter"),
    (PY_CLASS, "litestar.dto.base_factory.AbstractDTOFactory"),
    (PY_CLASS, "litestar.dto.factory.DTOConfig"),
    (PY_CLASS, "litestar.dto.factory.DTOData"),
    (PY_CLASS, "litestar.dto.interface.DTOInterface"),
    (PY_CLASS, "litestar.partial.Partial"),
    (PY_CLASS, "litestar.response.RedirectResponse"),
    (PY_CLASS, "litestar.response_containers.Redirect"),
    (PY_CLASS, "litestar.response_containers.Template"),
    (PY_CLASS, "litestar.contrib.sqlalchemy.types.BigIntIdentity"),
    (PY_CLASS, "litestar.contrib.sqlalchemy.types.JsonB"),
    (PY_CLASS, "litestar.typing.ParsedType"),
    (PY_METH, "litestar.dto.factory.DTOData.create_instance"),
    (PY_METH, "litestar.dto.interface.DTOInterface.data_to_encodable_type"),
    (PY_CLASS, "advanced_alchemy.repository.typing.ModelT"),
    (PY_OBJ, "advanced_alchemy.config.common.SessionMakerT"),
    (PY_OBJ, "advanced_alchemy.config.common.ConnectionT"),
    (PY_CLASS, "advanced_alchemy.extensions.litestar.plugins._slots_base.SlotsBase"),
    (PY_CLASS, "advanced_alchemy.config.EngineConfig"),
    (PY_CLASS, "advanced_alchemy.extensions.litestar.plugins.SQLAlchemyPlugin"),
    (PY_CLASS, "advanced_alchemy.extensions.litestar.plugins.SQLAlchemySerializationPlugin"),
    (PY_CLASS, "advanced_alchemy.extensions.litestar.plugins.SQLAlchemyInitPlugin"),
    (PY_CLASS, "advanced_alchemy.extensions.litestar.config.SQLAlchemySyncConfig"),
    (PY_CLASS, "advanced_alchemy.extensions.litestar.config.SQLAlchemyAsyncConfig"),
    (PY_METH, "advanced_alchemy.extensions.litestar.plugins.SQLAlchemySerializationPlugin.create_dto_for_type"),
    (PY_CLASS, "advanced_alchemy.config.AsyncSessionConfig"),
    (PY_CLASS, "advanced_alchemy.config.SyncSessionConfig"),
    (PY_CLASS, "advanced_alchemy.types.JsonB"),
    (PY_CLASS, "advanced_alchemy.types.BigIntIdentity"),
    (PY_FUNC, "sqlalchemy.get_engine"),
    (PY_ATTR, "advanced_alchemy.repository.AbstractAsyncRepository.id_attribute"),
    (PY_OBJ, "litestar.template.base.T_co"),
    ("py:exc", "RepositoryError"),
    ("py:exc", "InternalServerError"),
    ("py:exc", "HTTPExceptions"),
    (PY_CLASS, "litestar.template.Template"),
    (PY_CLASS, "litestar.middleware.compression.gzip_facade.GzipCompression"),
]

nitpick_ignore_regex = [
    (PY_ATTR, "litestar.repository.testing.AsyncGenericMockRepository.id_attribute"),
    (PY_ATTR, "litestar.repository.AbstractAsyncRepository.id_attribute"),
    (PY_ATTR, "litestar.repository.AbstractSyncRepository.id_attribute"),
    # (PY_ATTR, "litestar.repository.AsyncGenericMockRepository.id_attribute"),
    (PY_OBJ, r"typing\..*"),
    (PY_RE, r".*R_co"),
    (PY_RE, r".*UserType"),
    (PY_RE, r"ModelT"),
    (PY_RE, r"litestar.*\.T"),
    (PY_RE, r"litestar.contrib.sqlalchemy.repository.ModelT"),
    (PY_RE, r"litestar\.middleware\.session\.base\.BaseSessionBackendT"),
    (PY_RE, r"litestar\.types.*"),
    (PY_RE, r"httpx.*"),
    # type vars
    (PY_RE, r"litestar.middleware.session.base.ConfigT"),
    (PY_RE, r"litestar\.connection\.base\.AuthT"),
    (PY_RE, r"litestar\.connection\.base\.HandlerT"),
    (PY_RE, r"litestar\.connection\.base\.StateT"),
    (PY_RE, r"litestar\.connection\.base\.UserT"),
    (PY_RE, r"litestar\.pagination\.C"),
    (PY_RE, r"multidict\..*"),
    (PY_RE, r"advanced_alchemy.*\.T"),
    (PY_RE, r"advanced_alchemy\.config.common\.EngineT"),
    (PY_RE, r"advanced_alchemy\.config.common\.SessionT"),
    (PY_RE, r".*R"),
]

# Warnings about missing references to those targets in the specified location will be ignored.
# The source of the references is taken 1:1 from the warnings as reported by Sphinx, e.g
# **/litestar/testing/client/async_client.py:docstring of litestar.testing.AsyncTestClient.exit_stack:1: WARNING: py:class reference target not found: AsyncExitStack
# would be added as: "litestar.testing.AsyncTestClient.exit_stack": {"AsyncExitStack"},
ignore_missing_refs = {
    # No idea what autodoc is doing here. Possibly unfixable on our end
    "litestar.template.base.TemplateEngineProtocol.get_template": {"litestar.template.base.T_co"},
    "litestar.template": {"litestar.template.base.T_co"},
    "litestar.openapi.OpenAPIController.security": {"SecurityRequirement"},
    "litestar.response.file.async_file_iterator": {"FileSystemAdapter"},
    "advanced_alchemy._listeners.touch_updated_timestamp": {"Session"},
    re.compile("litestar.response.redirect.*"): {"RedirectStatusType"},
    re.compile(r"litestar\.plugins.*"): re.compile(".*ModelT"),
    re.compile(r"litestar\.(contrib|repository)\.*"): re.compile(".*T"),
    re.compile(r"litestar\.contrib\.sqlalchemy\.*"): re.compile(
        ".*(ConnectionT|EngineT|SessionT|SessionMakerT|SlotsBase)"
    ),
    re.compile(r"litestar\.dto.*"): re.compile(".*T|.*FieldDefinition|Empty"),
    re.compile(r"litestar\.template\.(config|TemplateConfig).*"): re.compile(".*EngineType"),
    "litestar.concurrency.set_asyncio_executor": {"ThreadPoolExecutor"},
    "litestar.concurrency.get_asyncio_executor": {"ThreadPoolExecutor"},
    re.compile(r"litestar\.channels\.backends\.asyncpg.*"): {"asyncpg.connection.Connection"},
}

# Do not warn about broken links to the following:
linkcheck_ignore = [
    r"http://localhost(:\d+)?",
    r"http://127.0.0.1(:\d+)?",
    "http://testserver",
]

auto_pytabs_min_version = (3, 8)
auto_pytabs_max_version = (3, 11)
auto_pytabs_compat_mode = True

autosectionlabel_prefix_document = True

suppress_warnings = [
    "autosectionlabel.*",
    "ref.python",  # TODO: remove when https://github.com/sphinx-doc/sphinx/issues/4961 is fixed
]

html_theme = "litestar_sphinx_theme"
html_static_path = ["_static"]
html_js_files = ["versioning.js"]
html_css_files = ["style.css"]
html_show_sourcelink = False
html_title = "Litestar Framework"

html_theme_options = {
    "use_page_nav": False,
    "github_repo_name": "litestar",
    "logo": {
        "link": "https://litestar.dev",
    },
    "pygment_light_style": "xcode",
    "pygment_dark_style": "lightbulb",
    "navigation_with_keys": True,
    "extra_navbar_items": {
        "Documentation": "index",
        "Community": {
            "Contributing": {
                "description": "Learn how to contribute to the Litestar project",
                "link": "https://docs.litestar.dev/latest/contribution-guide.html",
                "icon": "contributing",
            },
            "Code of Conduct": {
                "description": "Review the etiquette for interacting with the Litestar community",
                "link": "https://github.com/litestar-org/.github?tab=coc-ov-file",
                "icon": "coc",
            },
            "Security": {
                "description": "Overview of Litestar's security protocols",
                "link": "https://github.com/litestar-org/.github?tab=coc-ov-file#security-ov-file",
                "icon": "coc",
            },
        },
        "About": {
            "Litestar Organization": {
                "description": "Details about the Litestar organization",
                "link": "https://litestar.dev/about/organization",
                "icon": "org",
            },
            "Releases": {
                "description": "Explore the release process, versioning, and deprecation policy for Litestar",
                "link": "https://litestar.dev/about/litestar-releases",
                "icon": "releases",
            },
        },
        "Release notes": {
            "What's new in 2.0": "release-notes/whats-new-2",
            "2.x Changelog": "https://docs.litestar.dev/2/release-notes/changelog.html",
            "1.x Changelog": "https://docs.litestar.dev/1/release-notes/changelog.html",
        },
        "Help": {
            "Discord Help Forum": {
                "description": "Dedicated Discord help forum",
                "link": "https://discord.gg/litestar-919193495116337154",
                "icon": "coc",
            },
            "GitHub Discussions": {
                "description": "GitHub Discussions ",
                "link": "https://github.com/orgs/litestar-org/discussions",
                "icon": "coc",
            },
            "Stack Overflow": {
                "description": "We monitor the <code><b>litestar</b></code> tag on Stack Overflow",
                "link": "https://stackoverflow.com/questions/tagged/litestar",
                "icon": "coc",
            },
        },
    },
}


def update_html_context(
    app: Sphinx, pagename: str, templatename: str, context: dict[str, Any], doctree: document
) -> None:
    context["generate_toctree_html"] = partial(context["generate_toctree_html"], startdepth=0)


def delayed_setup(app: Sphinx) -> None:
    """
    When running linkcheck pydata_sphinx_theme causes a build failure, and checking
    the builder in the initial `setup` function call is not possible, so the check
    and extension setup has to be delayed until the builder is initialized.
    """
    if app.builder.name == "linkcheck":
        return

    app.setup_extension("pydata_sphinx_theme")
    app.connect("html-page-context", update_html_context)


def setup(app: Sphinx) -> dict[str, bool]:
    app.connect("builder-inited", delayed_setup, priority=0)

    app.setup_extension("litestar_sphinx_theme")

    return {"parallel_read_safe": True, "parallel_write_safe": True}
