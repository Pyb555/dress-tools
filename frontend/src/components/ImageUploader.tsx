import { useRef, useState, type DragEvent, type ChangeEvent } from "react";

interface Props {
  label: string;
  imageUrl: string | null;
  onImageChange: (file: File) => void;
  placeholder?: string;
}

/**
 * 图片上传组件：支持拖拽和点击上传
 */
export default function ImageUploader({ label, imageUrl, onImageChange, placeholder }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = (file: File) => {
    if (!file.type.startsWith("image/")) {
      alert("请上传图片文件");
      return;
    }
    onImageChange(file);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div className="image-uploader">
      <p className="uploader-label">{label}</p>
      <div
        className={`uploader-zone ${isDragging ? "dragging" : ""} ${imageUrl ? "has-image" : ""}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        {imageUrl ? (
          <img src={imageUrl} alt={label} className="uploader-preview" />
        ) : (
          <div className="uploader-placeholder">
            <span className="uploader-icon">📷</span>
            <span>{placeholder || "点击或拖拽上传图片"}</span>
          </div>
        )}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={handleChange}
        style={{ display: "none" }}
      />
    </div>
  );
}
