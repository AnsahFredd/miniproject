import { useDropzone } from "react-dropzone"
import { Upload } from "lucide-react"

type Props = {
  onDrop: (files: File[]) => void
}

const UploadDropzone = ({ onDrop }: Props) => {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
    maxSize: 50 * 1024 * 1024,
    multiple: false,
  })

  return (
    <div
      {...getRootProps()}
      className={`cursor-pointer border-2 border-dashed rounded-lg p-12 text-center transition-all duration-200 ${
        isDragActive
          ? "border-blue-400 bg-blue-50"
          : "border-gray-300 hover:border-gray-400 hover:bg-gray-50"
      }`}
    >
      <input {...getInputProps()} />
      <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        {isDragActive ? "Drop your document here" : "Drag & drop your document here"}
      </h3>
      <p className="text-sm text-gray-600 mb-2">Or click to browse files</p>
      <p className="text-xs text-gray-500">Supports PDF, DOCX, TXT • Maximum 50MB</p>
    </div>
  )
}

export default UploadDropzone
