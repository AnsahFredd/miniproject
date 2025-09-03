import React from 'react'

interface LoadingSkeletonProps {
    type?: 'page' | 'list' | 'auth' | 'card';
    className?: string
}


export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
    type = "page",
    className = ''
}) => {
    const baseClasses = "animate-pulse bg-gray-200 rounded";

    switch (type) {
        case 'auth':
        return (
            <div className={`min-h-screen flex items-center justify-center bg-gray-50 ${className}`}>
                <div className='max-w-md w-full bg-white shadow-lg rounded-lg p-6'>
                <div className={`${baseClasses} h-8 w-3/4 m-auto mb-6`}></div>
                <div className={`${baseClasses} h-12 w-full mb-4`}></div>
                 <div className={`${baseClasses} h-12 w-full mb-4`}></div>
                <div className={`${baseClasses} h-12 w-full mb-6`}></div>
                <div className={`${baseClasses} h-4 w-1/2 mx-auto`}></div>
                </div>
            </div>
        )

        case 'page':
            return (
                <div className={`min-h-screen bg-gray-50 ${className}`}>
                    <div className='max-w-7xl mx-auto py-6 sm:px-6 lg:px-8'>
                        <div className={`${baseClasses} h-8 w-1/4 mb-6`}></div>
                        <div className='grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3'>
                            {[...Array(6)].map((_, i) => (
                                <div key={i} className='bg-white rounded-lg shadow p-6'>
                                    <div className={`${baseClasses} h-6 w-3/4 mb-4`}></div>
                                     <div className={`${baseClasses} h-4 w-full mb-2`}></div>
                                     <div className={`${baseClasses} h-4 w-2/3`}></div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            );


        case 'card':
            return (
                <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
                    <div className={`${baseClasses} h-6 w-3/4 mb-4`}></div>
                    <div className={`${baseClasses} h-4 w-full mb-2`}></div>
                    <div className={`${baseClasses} h-4 w-2/3`}></div>
              </div>
              
            );
        
        case 'list':
            return (
                <div className={`space-y-4 ${className}`}>
                {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex items-center space-x-4 p-4 bg-white rounded-lg shadow">
                    <div className={`${baseClasses} h-12 w-12 rounded-full`}></div>
                    <div className="flex-1">
                        <div className={`${baseClasses} h-4 w-1/4 mb-2`}></div>
                        <div className={`${baseClasses} h-3 w-1/2`}></div>
                    </div>
                    </div>
                ))}
                </div>
      );

      default: 
        return <div className={`${baseClasses} h-64 w-full ${className}`}></div>
    }
}
