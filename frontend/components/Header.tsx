import React from 'react'
import Image from 'next/image'

export function Header() {
  return (
    <div className="text-center mb-16">
      <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-r from-blue-500 to-blue-600 p-2 mb-8">
        <Image
          src="/logo.png"
          alt="FollowNet Logo"
          width={64}
          height={64}
          className="w-16 h-16 object-contain"
        />
      </div>
      <h1 className="text-5xl font-bold text-gray-800 dark:text-white mb-6">FollowNet</h1>
      <p className="text-xl text-gray-600 dark:text-blue-200 max-w-2xl mx-auto">
        One-click scraping of social media platform follower data, supporting pagination and data export
      </p>
    </div>
  )
}