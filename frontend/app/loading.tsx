export default function GlobalLoading() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-24">
      <div className="mb-5 h-8 w-56 rounded-xl shimmer" />
      <div className="grid gap-5 md:grid-cols-3">
        <div className="h-48 rounded-2xl shimmer" />
        <div className="h-48 rounded-2xl shimmer" />
        <div className="h-48 rounded-2xl shimmer" />
      </div>
    </main>
  );
}
