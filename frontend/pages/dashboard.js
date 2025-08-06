import { useEffect, useState } from 'react';

export default function Dashboard() {
  const [picks, setPicks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPicks() {
      try {
        const res = await fetch((process.env.NEXT_PUBLIC_API_URL || '') + '/api/picks');
        const data = await res.json();
        setPicks(data);
      } catch (error) {
        console.error('Error fetching picks', error);
      } finally {
        setLoading(false);
      }
    }
    fetchPicks();
  }, []);

  return (
    <main className="min-h-screen p-4">
      <h1 className="text-3xl font-bold mb-4">Dashboard</h1>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="space-y-4">
          {picks.length === 0 ? (
            <p>No picks available.</p>
          ) : (
            picks.map((pick, index) => (
              <div key={index} className="p-4 border rounded-lg">
                <p className="font-semibold">{pick.title}</p>
                <p>{pick.description}</p>
                <p className="text-sm text-gray-500">Confidence: {pick.confidence}%</p>
              </div>
            ))
          )}
        </div>
      )}
    </main>
  );
}
