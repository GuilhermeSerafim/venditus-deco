class FakeLLM:
    """Dublê do LLM. with_structured_output devolve o próprio dublê."""

    def __init__(self, resposta):
        self.resposta = resposta
        self.prompt_recebido = None

    def with_structured_output(self, _schema):
        return self

    def invoke(self, prompt):
        self.prompt_recebido = prompt
        return self.resposta
