// src/components/ProfileImageUpload.tsx
import React, { useState } from 'react';

const ProfileImageUpload = () => {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const objectUrl = URL.createObjectURL(file);
      setPreviewUrl(objectUrl);
    }
  };

  return (
    <div className="w-full md:w-48 flex flex-col items-center justify-center bg-white p-6 md:p-8">
      <div className="w-24 h-24 md:w-32 md:h-32 rounded-full overflow-hidden border-4 border-blue-200 mb-4">
        <img
          src={
            previewUrl ||
            'https://images.unsplash.com/photo-1494790108755-2616b612b1e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
          }
          alt="Profile"
          className="w-full h-full object-cover"
        />
      </div>

      <label className="cursor-pointer bg-blue-600 text-white px-4 py-1 rounded text-sm hover:bg-blue-700">
        Change Photo
        <input
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          className="hidden"
        />
      </label>
    </div>
  );
};

export default ProfileImageUpload;
