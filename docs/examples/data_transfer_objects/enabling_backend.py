from litestar import Litestar
from litestar.config.app import ExperimentalFeatures

app = Litestar(experimental_features=[ExperimentalFeatures.DTO_CODEGEN])
