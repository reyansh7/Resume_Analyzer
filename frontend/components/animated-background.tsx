export function AnimatedBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute -left-24 top-24 h-72 w-72 rounded-full bg-indigo-300/30 blur-3xl animate-blob" />
      <div className="absolute right-10 top-40 h-80 w-80 rounded-full bg-cyan-300/30 blur-3xl animate-blob" style={{ animationDelay: "1s" }} />
      <div className="absolute bottom-0 left-1/3 h-96 w-96 rounded-full bg-violet-300/25 blur-3xl animate-blob" style={{ animationDelay: "2s" }} />
    </div>
  );
}
