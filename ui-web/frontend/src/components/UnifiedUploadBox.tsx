import { useState, useRef, useCallback } from 'react';

/**
 * Unified Upload Box Component
 * 
 * A comprehensive file upload component that supports:
 * - Drag and drop
 * - Click to browse
 * - Multiple file types (images, documents, audio, video)
 * - Progress indication
 * - File preview
 */

type FileType = 'image' | 'document' | 'audio' | 'video' | 'any';

type UploadFile = {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'complete' | 'error';
  error?: string;
  preview?: string;
};

type UnifiedUploadBoxProps = {
  acceptedTypes?: FileType[];
  maxFiles?: number;
  maxSizeMB?: number;
  onUpload?: (files: File[]) => Promise<void>;
  onRemove?: (fileId: string) => void;
  disabled?: boolean;
  className?: string;
};

const fileTypeConfig: Record<FileType, { accept: string; label: string; icon: string }> = {
  image: { accept: 'image/*', label: 'Images', icon: '🖼️' },
  document: { accept: '.pdf,.doc,.docx,.txt,.md', label: 'Documents', icon: '📄' },
  audio: { accept: 'audio/*', label: 'Audio', icon: '🎵' },
  video: { accept: 'video/*', label: 'Video', icon: '🎬' },
  any: { accept: '*/*', label: 'Files', icon: '📁' },
};

export default function UnifiedUploadBox({
  acceptedTypes = ['any'],
  maxFiles = 10,
  maxSizeMB = 50,
  onUpload,
  onRemove,
  disabled = false,
  className = '',
}: UnifiedUploadBoxProps) {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Build accept string from types
  const acceptString = acceptedTypes
    .map(type => fileTypeConfig[type].accept)
    .join(',');
  
  // Generate unique ID
  const generateId = () => `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  // Validate file
  const validateFile = (file: File): string | null => {
    // Check size
    if (file.size > maxSizeMB * 1024 * 1024) {
      return `File exceeds ${maxSizeMB}MB limit`;
    }
    
    // Check type if not accepting any
    if (!acceptedTypes.includes('any')) {
      const isValidType = acceptedTypes.some(type => {
        const config = fileTypeConfig[type];
        if (config.accept.startsWith('.')) {
          // Extension-based check
          const extensions = config.accept.split(',');
          return extensions.some(ext => file.name.toLowerCase().endsWith(ext));
        } else if (config.accept.endsWith('/*')) {
          // MIME type wildcard check
          const mimePrefix = config.accept.replace('/*', '');
          return file.type.startsWith(mimePrefix);
        }
        return file.type === config.accept;
      });
      
      if (!isValidType) {
        return 'File type not supported';
      }
    }
    
    return null;
  };
  
  // Create preview for images
  const createPreview = (file: File): Promise<string | undefined> => {
    return new Promise((resolve) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result as string);
        reader.onerror = () => resolve(undefined);
        reader.readAsDataURL(file);
      } else {
        resolve(undefined);
      }
    });
  };
  
  // Process files for upload
  const processFiles = useCallback(async (newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    
    // Check max files limit
    if (files.length + fileArray.length > maxFiles) {
      alert(`Maximum ${maxFiles} files allowed`);
      return;
    }
    
    const uploadFiles: UploadFile[] = [];
    
    for (const file of fileArray) {
      const error = validateFile(file);
      const preview = await createPreview(file);
      
      uploadFiles.push({
        id: generateId(),
        file,
        progress: 0,
        status: error ? 'error' : 'pending',
        error: error || undefined,
        preview,
      });
    }
    
    setFiles(prev => [...prev, ...uploadFiles]);
    
    // Trigger upload for valid files
    if (onUpload) {
      const validFiles = uploadFiles
        .filter(f => f.status !== 'error')
        .map(f => f.file);
      
      if (validFiles.length > 0) {
        // Update status to uploading
        setFiles(prev => prev.map(f => 
          validFiles.includes(f.file) ? { ...f, status: 'uploading' as const, progress: 0 } : f
        ));
        
        try {
          await onUpload(validFiles);
          
          // Update status to complete
          setFiles(prev => prev.map(f => 
            validFiles.includes(f.file) ? { ...f, status: 'complete' as const, progress: 100 } : f
          ));
        } catch (error) {
          // Update status to error
          setFiles(prev => prev.map(f => 
            validFiles.includes(f.file) 
              ? { ...f, status: 'error' as const, error: 'Upload failed' } 
              : f
          ));
        }
      }
    }
  }, [files.length, maxFiles, onUpload]);
  
  // Drag and drop handlers
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  };
  
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (!disabled && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };
  
  // Click to browse
  const handleClick = () => {
    if (!disabled) fileInputRef.current?.click();
  };
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  };
  
  // Remove file
  const handleRemove = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
    onRemove?.(fileId);
  };
  
  // Get file icon
  const getFileIcon = (file: File): string => {
    if (file.type.startsWith('image/')) return '🖼️';
    if (file.type.startsWith('audio/')) return '🎵';
    if (file.type.startsWith('video/')) return '🎬';
    if (file.type.includes('pdf')) return '📕';
    if (file.type.includes('word') || file.name.endsWith('.doc') || file.name.endsWith('.docx')) return '📘';
    return '📄';
  };
  
  // Format file size
  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };
  
  return (
    <div className={`w-full ${className}`}>
      {/* Drop zone */}
      <div
        onClick={handleClick}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
          transition-all duration-200
          ${isDragging 
            ? 'border-blue-500 bg-blue-50 scale-[1.02]' 
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptString}
          multiple={maxFiles > 1}
          onChange={handleFileChange}
          disabled={disabled}
          className="hidden"
        />
        
        <div className="flex flex-col items-center gap-3">
          <div className="text-4xl">
            {acceptedTypes.length === 1 
              ? fileTypeConfig[acceptedTypes[0]].icon 
              : '📁'
            }
          </div>
          
          <div>
            <p className="text-lg font-medium text-gray-700">
              {isDragging ? 'Drop files here' : 'Drag & drop files here'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              or click to browse
            </p>
          </div>
          
          <div className="flex flex-wrap justify-center gap-2 mt-2">
            {acceptedTypes.map(type => (
              <span
                key={type}
                className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
              >
                {fileTypeConfig[type].icon} {fileTypeConfig[type].label}
              </span>
            ))}
          </div>
          
          <p className="text-xs text-gray-400 mt-2">
            Max {maxFiles} file{maxFiles > 1 ? 's' : ''} • Up to {maxSizeMB}MB each
          </p>
        </div>
      </div>
      
      {/* File list */}
      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.map(uploadFile => (
            <div
              key={uploadFile.id}
              className={`
                flex items-center gap-3 p-3 rounded-lg border
                ${uploadFile.status === 'error' 
                  ? 'border-red-200 bg-red-50' 
                  : uploadFile.status === 'complete'
                    ? 'border-green-200 bg-green-50'
                    : 'border-gray-200 bg-white'
                }
              `}
            >
              {/* Preview or icon */}
              <div className="w-10 h-10 flex-shrink-0 rounded overflow-hidden bg-gray-100 flex items-center justify-center">
                {uploadFile.preview ? (
                  <img
                    src={uploadFile.preview}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-xl">{getFileIcon(uploadFile.file)}</span>
                )}
              </div>
              
              {/* File info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700 truncate">
                  {uploadFile.file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {formatSize(uploadFile.file.size)}
                  {uploadFile.error && (
                    <span className="text-red-500 ml-2">• {uploadFile.error}</span>
                  )}
                </p>
                
                {/* Progress bar */}
                {uploadFile.status === 'uploading' && (
                  <div className="mt-1 w-full h-1 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all duration-300"
                      style={{ width: `${uploadFile.progress}%` }}
                    />
                  </div>
                )}
              </div>
              
              {/* Status icon */}
              <div className="flex-shrink-0">
                {uploadFile.status === 'uploading' && (
                  <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                )}
                {uploadFile.status === 'complete' && (
                  <span className="text-green-500 text-xl">✓</span>
                )}
                {uploadFile.status === 'error' && (
                  <span className="text-red-500 text-xl">✗</span>
                )}
              </div>
              
              {/* Remove button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemove(uploadFile.id);
                }}
                className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


/**
 * Compact Upload Button
 * 
 * A smaller upload trigger for inline use.
 */

type CompactUploadProps = {
  label?: string;
  icon?: string;
  acceptedTypes?: FileType[];
  onUpload?: (files: File[]) => void;
  disabled?: boolean;
  className?: string;
};

export function CompactUploadButton({
  label = 'Upload',
  icon = '📎',
  acceptedTypes = ['any'],
  onUpload,
  disabled = false,
  className = '',
}: CompactUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const acceptString = acceptedTypes
    .map(type => fileTypeConfig[type].accept)
    .join(',');
  
  const handleClick = () => {
    if (!disabled) fileInputRef.current?.click();
  };
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload?.(Array.from(e.target.files));
    }
  };
  
  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      className={`
        inline-flex items-center gap-2 px-4 py-2 
        bg-gray-100 hover:bg-gray-200 
        text-gray-700 font-medium text-sm
        rounded-lg transition-colors
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
      `}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptString}
        multiple
        onChange={handleChange}
        disabled={disabled}
        className="hidden"
      />
      <span>{icon}</span>
      <span>{label}</span>
    </button>
  );
}
