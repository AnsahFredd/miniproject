import { File } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card"
import Button from "../ui/Button"
import { formatFileSize } from "../../utils/fileUtils"

type Props = {
  file: { name: string; size: number }
  isUploading: boolean
  onRemove: () => void
  onUpload: () => void
}

const SelectedFileCard = ({ file, isUploading, onRemove, onUpload }: Props) => (
  <Card>
    <CardHeader>
      <CardTitle className="text-lg">Selected File</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="flex items-center justify-between p-4 border rounded-lg bg-gray-50">
        <div className="flex items-center">
          <File className="w-5 h-5 mr-3 text-gray-500" />
          <div>
            <p className="font-medium text-gray-900">{file.name}</p>
            <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
          </div>
        </div>
        <Button onClick={onRemove} disabled={isUploading} label="Remove" />
      </div>

      <div className="flex justify-center mt-6">
        <Button
          onClick={onUpload}
          disabled={isUploading}
          className="min-w-[200px] btn btn-outline-accent text-white"
          label={isUploading ? "Validating Contract..." : "Upload & Validate"}
        />
      </div>
    </CardContent>
  </Card>
)

export default SelectedFileCard
