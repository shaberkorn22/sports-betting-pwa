import Head from 'next/head';

export default function Home() {
  return (
    <>
      <Head>
        <title>Sports Betting PWA</title>
        <meta name="description" content="Sports betting membership community" />
      </Head>
      <main className="min-h-screen flex flex-col items-center justify-center py-8 px-4">
        <h1 className="text-4xl font-bold mb-4 text-center">Welcome to Sports Betting PWA</h1>
        <p className="text-lg mb-6 text-center">
          Join our community of sports bettors to get daily picks, parlays, and analytics powered by AI.
        </p>
        <a href="/dashboard" className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg transition">
          Go to Dashboard
        </a>
      </main>
    </>
  );
}
