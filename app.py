from agentwhite import server
from agentwhite.setup_prompt import SETUP_PROMPT_HTML


if SETUP_PROMPT_HTML not in server.HTML:
    server.HTML = server.HTML.replace("</body>", SETUP_PROMPT_HTML + "</body>")


if __name__ == "__main__":
    server.main()
