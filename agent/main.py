"""CLI entry point.

Usage:
    python -m agent.main             # interactive text mode
    python -m agent.main --voice     # hands-free voice mode (Phase 2)
    python -m agent.main --daemon    # background autonomous mode (Phase 4)
    python -m agent.main --web       # animated browser chat UI
"""

import sys

from agent.graph import build_graph


def run_text_mode():
    print("Jarvis Agent — text mode. Type 'exit' to quit.\n")
    app = build_graph()

    from agent import session

    history = session.load_history()
    if history:
        print(f"(Resumed with {len(history)} messages from your last session.)\n")

    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if user_input.lower() in {"exit", "quit"}:
            print("Exiting.")
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})
        result = app.invoke({"messages": history, "iterations": 0})
        history = result["messages"]

        final_message = history[-1]
        content = getattr(final_message, "content", str(final_message))
        print(f"jarvis> {content}\n")

        # Persist after every turn (crash-safe) and summarize if it's grown long.
        history = session.maybe_summarize(history)
        session.save_history(history)


def main():
    if "--voice" in sys.argv:
        from agent.voice.voice_loop import run_voice_loop

        run_voice_loop()
    elif "--daemon" in sys.argv:
        from agent.daemon import run_daemon

        run_daemon()
    elif "--web" in sys.argv:
        from agent.webui.server import run_web

        run_web()
    else:
        run_text_mode()


if __name__ == "__main__":
    main()
