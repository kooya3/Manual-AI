import React, { useEffect, useState } from 'react';
import { useSupabaseClient } from '@supabase/auth-helpers-react';

const ManualList: React.FC = () => {
  const supabase = useSupabaseClient();
  const [manuals, setManuals] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchManuals = async () => {
      const { data, error } = await supabase.storage.from('manuals').list('manuals');

      if (error) {
        setError(error.message);
      } else {
        setManuals(data.map((file) => file.name));
      }
    };

    fetchManuals();
  }, [supabase]);

  return (
    <div>
      <h2>Uploaded Manuals</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <ul>
        {manuals.map((manual) => (
          <li key={manual}>
            <a
              href={`https://<your-supabase-url>.supabase.co/storage/v1/object/public/manuals/manuals/${manual}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              {manual}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ManualList;
