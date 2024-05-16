app = Litestar(lifespan=[ctx_a, ctx_b], on_shutdown=[hook_a, hook_b])
