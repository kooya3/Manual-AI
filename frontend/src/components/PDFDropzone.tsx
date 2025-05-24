import React, { useState } from 'react';
import { useSupabaseClient } from '@supabase/auth-helpers-react';

const PDFDropzone: React.FC = () => {
  const supabase = useSupabaseClient();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = async (file: File) => {
    if (file.size > 6 * 1024 * 1024) {
      setError('File size exceeds 6MB limit.');
      return;
    }

    setUploading(true);
    setError(null);

    const filePath = `manuals/${file.name}`;

    const { data, error: uploadError } = await supabase.storage
      .from('manuals')
      .upload(filePath, file, {
        upsert: true,
      });

    if (uploadError) {
      setError(uploadError.message);
    } else {
      console.log('File uploaded successfully:', data);
    }

    setUploading(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  return (
    <div
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      style={{
        border: '2px dashed #ccc',
        padding: '20px',
        textAlign: 'center',
        cursor: 'pointer',
      }}
    >
      {uploading ? (
        <p>Uploading... {progress}%</p>
      ) : (
        <p>Drag and drop a PDF file here, or click to select one.</p>
      )}
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
};

export default PDFDropzone;