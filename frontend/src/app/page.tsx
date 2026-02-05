import Image from "next/image";
import { ChatWidget } from "../components/chat/ChatWidget";

export default function Home() {
  return (
    <div className="page">
      <main className="hero">
        <Image
          className="hero__image"
          src="/frontpage.jpg"
          alt="Front page"
          fill
          priority
          sizes="100vw"
        />
      </main>
      <ChatWidget />
    </div>
  );
}
