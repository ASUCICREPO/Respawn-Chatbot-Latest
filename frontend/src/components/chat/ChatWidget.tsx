"use client";

import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import type { ChatMessage } from "../../types/chat";

type Language = "en" | "es";

function newId(): string {
  // crypto.randomUUID is available in modern browsers; fallback for older ones.
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function now(): number {
  return Date.now();
}

const SPANISH_HINTS = [
  "¿",
  "¡",
  "á",
  "é",
  "í",
  "ó",
  "ú",
  "ñ",
  "cómo",
  "qué",
  "por qué",
  "dónde",
  "cuándo",
  "paciente",
  "terapia",
  "rehabilitación",
  "juego",
  "juegos"
];

function detectLanguage(text: string, fallback: Language): Language {
  const lower = text.toLowerCase();
  if (SPANISH_HINTS.some((hint) => lower.includes(hint))) return "es";
  return fallback;
}

const SECTION_LABELS: Record<Language, string[]> = {
  en: ["Summary", "Recommendations", "Why this helps", "Next questions"],
  es: ["Resumen", "Recomendaciones", "Por qué ayuda", "Siguientes preguntas"]
};

type ParsedAssistant = {
  nodes: React.ReactElement[];
  nextQuestions: string[];
};

function inferLanguageFromContent(content: string, fallback: Language): Language {
  if (content.includes("Resumen:") || content.includes("Siguientes preguntas:")) return "es";
  if (content.includes("Summary:") || content.includes("Next questions:")) return "en";
  return fallback;
}

function parseAssistantContent(content: string, language: Language): ParsedAssistant {
  const cleaned = content
    .replace(/\r\n/g, "\n")
    .replace(/^\s*Action:.*$/gim, "")
    .replace(/^\s*Response:\s*/gim, "")
    .replace(/\*\*/g, "")
    .trim();
  const lines = cleaned ? cleaned.split("\n") : [];
  const nodes: JSX.Element[] = [];
  const nextQuestions: string[] = [];
  let i = 0;
  let currentSection: string | null = null;
  const nextLabel = language === "es" ? "Siguientes preguntas" : "Next questions";

  const recommendationsLabel = language === "es" ? "Recomendaciones" : "Recommendations";

  while (i < lines.length) {
    const rawLine = lines[i] ?? "";
    const line = rawLine.trim();

    if (!line) {
      nodes.push(<div key={`spacer-${i}`} className="chatWidget__spacer" />);
      i += 1;
      continue;
    }

    const labelMatch = line.match(/^([A-Za-zÁÉÍÓÚÑáéíóúüÜ\s]+):\s*(.*)$/);
    if (labelMatch) {
      const label = labelMatch[1].trim();
      const rest = labelMatch[2]?.trim();
      const isSection = SECTION_LABELS[language]?.includes(label);
      if (isSection) {
        currentSection = label;
        const isNextSection = label === nextLabel;
        if (!isNextSection) {
          nodes.push(
            <div
              key={`label-${i}`}
              className={`chatWidget__sectionTitle${
                label === recommendationsLabel ? " chatWidget__sectionTitle--recommendations" : ""
              }`}
            >
              {label}
            </div>
          );
          if (rest) {
            nodes.push(
              <div key={`label-text-${i}`} className="chatWidget__sectionText">
                {rest}
              </div>
            );
          }
        }
        i += 1;
        continue;
      }
    }

    if (line.startsWith("- ") || line.startsWith("• ")) {
      const items: string[] = [];
      while (i < lines.length) {
        const bulletLine = (lines[i] ?? "").trim();
        if (bulletLine.startsWith("- ") || bulletLine.startsWith("• ")) {
          const item = bulletLine.replace(/^[-•]\s*/, "");
          items.push(item);
          if (currentSection === nextLabel && item) {
            nextQuestions.push(item);
          }
          i += 1;
          continue;
        }
        break;
      }
      if (currentSection !== nextLabel) {
        nodes.push(
          <ul key={`list-${i}`} className="chatWidget__bulletList">
            {items.map((item, idx) => (
              <li key={`item-${i}-${idx}`}>{item}</li>
            ))}
          </ul>
        );
      }
      continue;
    }

    nodes.push(
      <p key={`p-${i}`} className="chatWidget__paragraph">
        {line}
      </p>
    );
    i += 1;
  }

  if (nodes.length === 0 && cleaned) {
    nodes.push(
      <p key="fallback-text" className="chatWidget__paragraph">
        {cleaned}
      </p>
    );
  }

  return { nodes, nextQuestions };
}

function ChatIcon({ size = 28 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M20 12c0 3.866-3.582 7-8 7a9.8 9.8 0 0 1-2.118-.23L4 20l1.445-3.612A6.83 6.83 0 0 1 4 12c0-3.866 3.582-7 8-7s8 3.134 8 7Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path
        d="M8.25 12h.01M12 12h.01M15.75 12h.01"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 12l17-8-6 18-3-7-8-3Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function RefreshIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 12a8 8 0 1 0 2.34-5.66"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M4 19v-5h5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function FaqIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M20 12c0 3.866-3.582 7-8 7a9.8 9.8 0 0 1-2.118-.23L4 20l1.445-3.612A6.83 6.83 0 0 1 4 12c0-3.866 3.582-7 8-7s8 3.134 8 7Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="M8.25 12h.01M12 12h.01M15.75 12h.01"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}
const FAQ_EN: string[] = [
  "I've never used adaptive gaming in therapy/rehabilitation, where do I start?",
  "What games/platforms/systems work best for patients with limited mobility?",
  "How do I choose the right adaptive controller/setup for my patient's motor abilities?",
  "How do I balance a patient's physical limitations with their desired play style or preferred games/game genres?",
  "How do I help a patient develop mastery in one game and then transfer those skills to another game with different demands and objectives?",
  "What game genres are easiest to adapt for patients with severe physical limitations, decreased strength or limited range of motion?",
  "How do I decide where to place controls for optimal activation?",
  "How do I prioritize which controls or actions should be easiest for the patient to access in a game?",
  "Why does my patient perform well in one game but poorly in another, even with the same setup?",
  "How can I design a setup that works across multiple games?"
];

// Spanish translations of the provided FAQs (human-friendly, not literal word-for-word).
const FAQ_ES: string[] = [
  "Nunca he usado juegos adaptativos en terapia/rehabilitación. ¿Por dónde empiezo?",
  "¿Qué juegos/plataformas/sistemas funcionan mejor para pacientes con movilidad limitada?",
  "¿Cómo elijo el controlador adaptativo/la configuración adecuada según las habilidades motoras de mi paciente?",
  "¿Cómo equilibro las limitaciones físicas de un paciente con su estilo de juego o sus géneros/juegos preferidos?",
  "¿Cómo ayudo a un paciente a dominar un juego y luego transferir esas habilidades a otro con diferentes exigencias y objetivos?",
  "¿Qué géneros de videojuegos son más fáciles de adaptar para pacientes con limitaciones físicas severas, poca fuerza o rango de movimiento limitado?",
  "¿Cómo decido dónde colocar los controles para una activación óptima?",
  "¿Cómo priorizo qué controles o acciones deben ser los más fáciles de acceder para el paciente dentro de un juego?",
  "¿Por qué mi paciente rinde bien en un juego pero mal en otro, incluso con la misma configuración?",
  "¿Cómo puedo diseñar una configuración que funcione en varios juegos?"
];

export function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [language, setLanguage] = useState<Language>("en");
  const [messages, setMessages] = useState<ChatMessage[]>(() => []);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [lastUserLanguage, setLastUserLanguage] = useState<Language>("en");
  const [isFaqOpen, setIsFaqOpen] = useState(true);

  const listRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const canSend = useMemo(
    () => !isSending && draft.trim().length > 0,
    [draft, isSending]
  );

  useEffect(() => {
    if (!isOpen) return;
    // Focus input when opening.
    inputRef.current?.focus();
  }, [isOpen]);

  useEffect(() => {
    // Keep scrolled to the newest message.
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, isOpen]);

  const ui = useMemo(() => {
    const isEs = language === "es";
    return {
      title: isEs ? "Tu guía de juegos adaptativos" : "Your Adaptive Gaming Guide",
      faqHeading: "FAQ",
      emptyTitle: isEs ? "Inicia una conversación" : "Start a conversation",
      emptySubtitle: isEs
        ? "Selecciona una pregunta del panel o escribe la tuya abajo"
        : "Select a question from the sidebar or type your own below",
      inputPlaceholder: isEs
        ? "Haz una pregunta sobre juegos adaptativos..."
        : "Ask a question about adaptive gaming...",
      openLabel: isEs ? "Abrir chat" : "Open chat",
      closeLabel: isEs ? "Cerrar chat" : "Close chat",
      typing: isEs ? "Pensando" : "Thinking",
      clearChat: isEs ? "Borrar chat" : "Clear chat",
      hideFaq: isEs ? "Ocultar FAQ" : "Hide FAQ",
      showFaq: isEs ? "Mostrar FAQ" : "Show FAQ"
    };
  }, [language]);

  const faqs = useMemo(() => (language === "es" ? FAQ_ES : FAQ_EN), [language]);

  useEffect(() => {
    if (!isOpen) return;
    setMessages([]);
    setConversationId(undefined);
    setDraft("");
    setLastUserLanguage(language);
  }, [language, isOpen]);

  async function send(text: string) {
    if (!text || isSending) return;
    const inferredLanguage = detectLanguage(text, language);

    const userMsg: ChatMessage = {
      id: newId(),
      role: "user",
      content: text,
      createdAt: now()
    };

    setLastUserLanguage(inferredLanguage);
    setIsSending(true);
    setIsStreaming(false);
    setMessages((prev) => [...prev, userMsg]);

    try {
      const assistantId = newId();
      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: "assistant", content: "", createdAt: now() }
      ]);

      // Resolve API base URL for local/dev/prod usage.
      const base =
        process.env.NEXT_PUBLIC_API_URL?.trim()?.replace(/\/$/, "") ||
        (typeof window !== "undefined" ? window.location.origin : "http://localhost:8000");
      const chatUrl = `${base}/api/chat`;

      const chatRes = await fetch(chatUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, conversationId, language: inferredLanguage })
      });

      if (!chatRes.ok) {
        const errorText = await chatRes.text().catch(() => "");
        const suffix = errorText ? `: ${errorText}` : "";
        throw new Error(`Chat failed (${chatRes.status})${suffix}`);
      }

      const data = await chatRes.json();
      setConversationId(data.conversationId);
      
      // Update the assistant message with the full response
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, content: data.reply } : m))
      );
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : "Sorry — something went wrong sending that message.";
      setConversationId(undefined);
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: "assistant",
          content: `Error: ${msg}`,
          createdAt: now()
        }
      ]);
    } finally {
      setIsSending(false);
      setIsStreaming(false);
      inputRef.current?.focus();
    }
  }

  async function onSendDraft() {
    const text = draft.trim();
    if (!text) return;
    setDraft("");
    await send(text);
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      void onSendDraft();
    }
  }

  function onFaqClick(question: string) {
    if (!isOpen) setIsOpen(true);
    setDraft("");
    void send(question);
  }

  function clearChat() {
    setMessages([]);
    setConversationId(undefined);
    setDraft("");
    inputRef.current?.focus();
  }

  return (
    <div className="chatWidget" aria-live="polite">
      <button
        type="button"
        className="chatWidget__fab"
        aria-label={isOpen ? ui.closeLabel : ui.openLabel}
        aria-expanded={isOpen}
        onClick={() => setIsOpen((v) => !v)}
      >
        <ChatIcon size={30} />
      </button>

      {isOpen ? (
        <div className="chatWidget__overlay" onMouseDown={() => setIsOpen(false)}>
          <section
            className="chatWidget__modal"
            role="dialog"
            aria-modal="true"
            aria-label={ui.title}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <header className="chatWidget__modalHeader">
              <div className="chatWidget__brand">
                <div className="chatWidget__brandIcon" aria-hidden="true">
                  <Image
                    className="chatWidget__brandLogo"
                    src="/ReSpawn_logo.png"
                    alt=""
                    width={36}
                    height={36}
                  />
                </div>
                <div className="chatWidget__brandTitle">{ui.title}</div>
              </div>

              <div className="chatWidget__headerRight">
                <div className="chatWidget__lang" role="group" aria-label="Language">
                  <button
                    type="button"
                    className={`chatWidget__langBtn ${
                      language === "en" ? "chatWidget__langBtn--active" : ""
                    }`}
                    onClick={() => setLanguage("en")}
                  >
                    EN
                  </button>
                  <button
                    type="button"
                    className={`chatWidget__langBtn ${
                      language === "es" ? "chatWidget__langBtn--active" : ""
                    }`}
                    onClick={() => setLanguage("es")}
                  >
                    ES
                  </button>
                </div>

                <button
                  type="button"
                  className="chatWidget__closeX"
                  aria-label={ui.closeLabel}
                  onClick={() => setIsOpen(false)}
                >
                  <span aria-hidden="true">×</span>
                </button>
              </div>
            </header>

            <div
              className={`chatWidget__layout ${
                isFaqOpen ? "" : "chatWidget__layout--faqHidden"
              }`}
            >
              {!isFaqOpen ? (
                <div className="chatWidget__faqRail" aria-hidden="true">
                  <button
                    type="button"
                    className="chatWidget__faqRailBtn"
                    onClick={() => setIsFaqOpen(true)}
                    aria-label={ui.showFaq}
                  >
                    <FaqIcon />
                    <span className="chatWidget__faqToggleTooltip chatWidget__faqToggleTooltip--right">
                      › {ui.showFaq}
                    </span>
                  </button>
                </div>
              ) : null}
              <aside className="chatWidget__sidebar" aria-label="FAQ">
                <div className="chatWidget__sidebarHeader">
                  <div className="chatWidget__sidebarTitle">
                    {ui.faqHeading}
                    <span className="chatWidget__faqBadge" aria-hidden="true">
                      <FaqIcon />
                    </span>
                  </div>
                  <button
                    type="button"
                    className="chatWidget__faqToggle"
                    onClick={() => setIsFaqOpen((prev) => !prev)}
                    aria-label={isFaqOpen ? ui.hideFaq : ui.showFaq}
                  >
                    {isFaqOpen ? "‹" : "›"}
                    <span className="chatWidget__faqToggleTooltip">
                      {isFaqOpen ? ui.hideFaq : ui.showFaq}
                    </span>
                  </button>
                </div>
                <div className="chatWidget__faqList">
                  {faqs.map((q) => (
                    <button
                      key={q}
                      type="button"
                      className="chatWidget__faqItem"
                      onClick={() => onFaqClick(q)}
                      disabled={isSending}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </aside>

              <main className="chatWidget__main">
                <div className="chatWidget__messagesWide" ref={listRef}>
                  {messages.length === 0 ? (
                    <div className="chatWidget__empty">
                      <div className="chatWidget__emptyTitle">{ui.emptyTitle}</div>
                      <div className="chatWidget__emptySubtitle">{ui.emptySubtitle}</div>
                    </div>
                  ) : (
                    <>
                      {messages.map((m) => {
                        const isAssistant = m.role === "assistant";
                        if (isAssistant && !m.content.trim() && isSending && !isStreaming) {
                          return null;
                        }
                        const parsed = isAssistant
                          ? parseAssistantContent(
                              m.content,
                              inferLanguageFromContent(m.content, lastUserLanguage)
                            )
                          : null;
                        const nextQuestions = parsed?.nextQuestions ?? [];
                        const uniqueQuestions = Array.from(new Set(nextQuestions)).slice(0, 2);

                        return (
                          <div
                            key={m.id}
                            className={`chatWidget__msg chatWidget__msg--${m.role}`}
                          >
                            <div className="chatWidget__msgBody">
                              <div className="chatWidget__bubbleWide">
                                {isAssistant ? (
                                  <div className="chatWidget__formatted">{parsed?.nodes}</div>
                                ) : (
                                  m.content
                                )}
                              </div>
                              {isAssistant && uniqueQuestions.length > 0 ? (
                                <div className="chatWidget__suggestions">
                                  {uniqueQuestions.map((suggestion) => (
                                    <button
                                      key={`${m.id}-${suggestion}`}
                                      type="button"
                                      className="chatWidget__suggestionChip"
                                      onClick={() => void send(suggestion)}
                                      disabled={isSending}
                                    >
                                      {suggestion}
                                    </button>
                                  ))}
                                </div>
                              ) : null}
                            </div>
                          </div>
                        );
                      })}
                      {isSending && !isStreaming ? (
                        <div className="chatWidget__msg chatWidget__msg--assistant">
                          <div className="chatWidget__bubbleWide chatWidget__bubbleWide--typing">
                            <span>{ui.typing}</span>
                            <span className="chatWidget__typingDots" aria-hidden="true">
                              <span />
                              <span />
                              <span />
                            </span>
                          </div>
                        </div>
                      ) : null}
                    </>
                  )}
                </div>

                <footer className="chatWidget__composerWide">
                  <input
                    ref={inputRef}
                    className="chatWidget__inputWide"
                    value={draft}
                    placeholder={ui.inputPlaceholder}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={onKeyDown}
                    disabled={isSending}
                  />
                  <button
                    type="button"
                    className="chatWidget__sendIcon"
                    onClick={() => void onSendDraft()}
                    disabled={!canSend}
                    aria-label="Send"
                  >
                    <SendIcon />
                  </button>
                  {messages.length > 0 ? (
                    <div className="chatWidget__clearWrap">
                      <button
                        type="button"
                        className="chatWidget__clearBtn"
                        onClick={clearChat}
                        aria-label={ui.clearChat}
                        disabled={isSending}
                      >
                        <RefreshIcon />
                      </button>
                      <span className="chatWidget__clearTooltip">{ui.clearChat}</span>
                    </div>
                  ) : null}
                </footer>
              </main>
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}


