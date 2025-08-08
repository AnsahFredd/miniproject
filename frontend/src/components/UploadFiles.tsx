import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File } from 'lucide-react';
import Button from '../components/ui/Button';
import axios from 'axios';
import {  useNavigate } from 'react-router-dom';


type UploadedFile = {
  name: string;
  size: number;
  file: File;
};

const API = import.meta.env.VITE_API_BASE_URL;

const UploadFiles: React.FC = () => {
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const navigate = useNavigate();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const validFormats = ['pdf', 'docx', 'txt'];
    const maxSize = 50 * 1024 * 1024;

    if (acceptedFiles.length === 0) return; // no files dropped

    const file = acceptedFiles[0]; // only take first file because multiple: false

    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!extension || !validFormats.includes(extension)) {
      alert(`Invalid file format. Upload PDF, DOCX, or TXT only.`);
      return;
    }

    if (file.size > maxSize) {
      alert(`File ${file.name} exceeds 50MB limit.`);
      return;
    }

    setUploadedFile({
      name: file.name,
      size: file.size,
      file,
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxSize: 50 * 1024 * 1024,
    multiple: false, // only allow one file
  });

  const handleUpload = async () => {
    if (!uploadedFile) {
      alert('No file to upload.');
      return;
    }

    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('user_id');

    if (!token || !userId) {
      alert('You must be logged in to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file', uploadedFile.file);
    formData.append('user_id', userId);

    setIsUploading(true);
    try {
       console.log('[UPLOAD] Starting upload for:', uploadedFile.name);
      const response = await axios.post(`${API}/documents/upload`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });

      console.log('[UPLOAD] Upload response:', response);

      if (response.status === 200) {
        console.log('Upload response:', response.data);
        
        // Try multiple possible response formats
        const documentId = response.data?.document_id || 
                          response.data?.id || 
                          response.data?.documentId ||
                          response.data?.file_id ||
                          response.data?.fileId ||
                          response.data?.data?.id ||
                          response.data?.data?.document_id;
        
        if (documentId) {
          console.log('Found document ID:', documentId);
          navigate(`/document/${documentId}/review`, { replace: true });
        } else {
            // Fallback: fetch user's documents and get the most recent one

          console.log('No document ID in response, fetching recent documents...');
          try {
            const documentsResponse = await axios.get(`${API}/documents/`, {
              headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
            });


            console.log('[DOCUMENTS] Fetched documents:', documentsResponse.data);

            
            if (documentsResponse.data && documentsResponse.data.length > 0) {
              // Get the most recent document (assuming they're sorted by upload time)
              const recentDocument = documentsResponse.data[0];
              const recentDocId = recentDocument.id || recentDocument.document_id || recentDocument._id;
              
              if (recentDocId) {
                console.log('Found recent document ID:', recentDocId);
                navigate(`/document/${recentDocId}/review`, { replace: true });
              } else {
                alert('File uploaded successfully!');
                navigate('/document', { replace: true });
              }
            } else {
              alert('File uploaded successfully!');
              navigate('/document', {replace: true });
            }
          } catch (fetchError) {
            console.error('Error fetching documents:', fetchError);
            alert('File uploaded successfully!');
            navigate('/document', {replace: true });
          }
        }
        
        setUploadedFile(null);
      }
    } catch (err: any) {
      console.error(err);
      alert(err?.response?.data?.detail || 'Upload failed.');
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white">
      <h1 className="text-2xl font-semibold text-[var(--color-primary)] mb-8">Upload Legal Document</h1>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`cursor-pointer border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          isDragActive ? 'border-[var(--color-accent)] bg-[color:rgb(20_184_166_/_8%)]' : 'border-gray-300 bg-[var(--bg-soft)] hover:border-[var(--color-secondary)]/40'
        }`}
        role="button"
        aria-label="Upload a document. Drag and drop or press Enter to browse files."
        tabIndex={0}
      >
        <input {...getInputProps()} aria-label="Document file input" />
        <Upload className="mx-auto h-12 w-12 text-[var(--color-secondary)] mb-4" />
        <p className="text-lg text-[var(--color-secondary)] mb-2">Drag & drop your document here</p>
        <p className="text-sm text-[var(--color-secondary)]/80">
          Or click to browse. PDF, DOCX, TXT. Max: 50MB.
        </p>
      </div>

      {/* Selected File */}
      {uploadedFile && (
        <div className="mt-8">
          <h2 className="text-lg font-medium text-[var(--color-primary)] mb-4">Selected File</h2>
          <div className="flex items-center justify-between p-3 bg-[var(--bg-soft)] rounded-md border border-gray-200">
            <div className="flex items-center">
              <File className="h-5 w-5 text-[var(--color-secondary)] mr-3" />
              <div>
                <p className="text-sm font-medium text-[var(--color-primary)]">{uploadedFile.name}</p>
                <p className="text-xs text-[var(--color-secondary)]">{formatFileSize(uploadedFile.size)}</p>
              </div>
            </div>
            <button
              onClick={() => setUploadedFile(null)}
              className="text-[var(--color-primary)] hover:opacity-80 text-sm font-medium"
            >
              Remove
            </button>
          </div>

          {/* Upload Button */}
          <div className="mt-6 flex justify-center">
            <Button
              label="Upload"
              isLoading={isUploading}
              onClick={handleUpload}
              otherStyles="btn btn-primary"
              animationStyles="hover:scale-105 active:scale-95 transition-transform duration-200 ease-in-out"
            />
          </div>
        </div>
      )}

    </div>
  );
};

export default UploadFiles;
