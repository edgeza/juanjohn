'use client';

import { useState } from 'react';
import { GraduationCap, BookOpen, Video, Users, Star, Clock, Play } from 'lucide-react';

export default function Tutorials() {
  const [selectedCategory, setSelectedCategory] = useState('all');

  const categories = [
    { id: 'all', name: 'All Courses' },
    { id: 'beginner', name: 'Beginner' },
    { id: 'intermediate', name: 'Intermediate' },
    { id: 'advanced', name: 'Advanced' },
    { id: 'trading', name: 'Trading Strategies' },
    { id: 'analysis', name: 'Technical Analysis' }
  ];

  const courses = [
    {
      id: 1,
      title: 'Introduction to Trading Fundamentals',
      description: 'Learn the basics of financial markets, trading terminology, and risk management principles.',
      category: 'beginner',
      duration: '2 hours',
      rating: 4.8,
      students: 1247,
      thumbnail: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
      instructor: 'Sarah Johnson',
      price: 'Free'
    },
    {
      id: 2,
      title: 'Technical Analysis Masterclass',
      description: 'Master chart patterns, indicators, and advanced technical analysis techniques.',
      category: 'intermediate',
      duration: '4 hours',
      rating: 4.9,
      students: 892,
      thumbnail: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
      instructor: 'Michael Chen',
      price: '$49'
    },
    {
      id: 3,
      title: 'Advanced Portfolio Management',
      description: 'Learn sophisticated portfolio optimization strategies and risk management techniques.',
      category: 'advanced',
      duration: '6 hours',
      rating: 4.7,
      students: 456,
      thumbnail: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
      instructor: 'Dr. Robert Smith',
      price: '$99'
    },
    {
      id: 4,
      title: 'Cryptocurrency Trading Strategies',
      description: 'Explore crypto-specific trading strategies and market dynamics.',
      category: 'trading',
      duration: '3 hours',
      rating: 4.6,
      students: 678,
      thumbnail: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
      instructor: 'Alex Thompson',
      price: '$39'
    },
    {
      id: 5,
      title: 'Forex Market Analysis',
      description: 'Comprehensive guide to forex trading and currency pair analysis.',
      category: 'analysis',
      duration: '5 hours',
      rating: 4.8,
      students: 1023,
      thumbnail: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
      instructor: 'Emma Wilson',
      price: '$69'
    },
    {
      id: 6,
      title: 'Risk Management Essentials',
      description: 'Essential risk management strategies for successful trading.',
      category: 'beginner',
      duration: '2.5 hours',
      rating: 4.9,
      students: 1567,
      thumbnail: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
      instructor: 'David Brown',
      price: 'Free'
    }
  ];

  const filteredCourses = selectedCategory === 'all' 
    ? courses 
    : courses.filter(course => course.category === selectedCategory);

  return (
    <div className="min-h-screen p-8 transition-all duration-500" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 slide-in">
          <div className="flex items-center gap-4 mb-4">
            <div className="rounded-xl p-3 transition-colors duration-300" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
              <GraduationCap className="h-8 w-8" style={{ color: 'var(--accent-color)' }} />
            </div>
            <div>
              <h1 className="text-3xl font-bold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Education Center
              </h1>
              <p className="mt-2 transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Master trading with our comprehensive educational resources
              </p>
            </div>
          </div>
        </div>

        {/* Categories */}
        <div className="mb-8">
          <div className="flex flex-wrap gap-4">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`px-6 py-3 rounded-2xl text-sm font-medium transition-all duration-300 ${
                  selectedCategory === category.id
                    ? 'glass-hover'
                    : 'hover:opacity-80'
                }`}
                style={{
                  backgroundColor: selectedCategory === category.id ? 'var(--glass-bg)' : 'var(--bg-secondary)',
                  color: selectedCategory === category.id ? 'var(--text-primary)' : 'var(--text-secondary)',
                  border: selectedCategory === category.id ? '1px solid var(--glass-border)' : 'none',
                }}
              >
                {category.name}
              </button>
            ))}
          </div>
        </div>

        {/* Featured Course */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-6 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
            Featured Course
          </h2>
          <div className="card glass-hover">
            <div className="flex items-center gap-6">
              <div className="relative">
                <div
                  className="w-64 h-40 bg-center bg-no-repeat bg-cover rounded-xl"
                  style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80")' }}
                ></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="rounded-full p-4" style={{ backgroundColor: 'rgba(0, 0, 0, 0.7)' }}>
                    <Play className="h-8 w-8 text-white" />
                  </div>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                  Complete Trading Masterclass
                </h3>
                <p className="text-base transition-colors duration-300 mb-4" style={{ color: 'var(--text-secondary)' }}>
                  A comprehensive course covering everything from basic concepts to advanced trading strategies. Perfect for both beginners and experienced traders.
                </p>
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4" style={{ color: 'var(--text-secondary)' }} />
                    <span className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>12 hours</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Star className="h-4 w-4" style={{ color: '#ffaa00' }} />
                    <span className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>4.9 (2,847 reviews)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4" style={{ color: 'var(--text-secondary)' }} />
                    <span className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>15,234 students</span>
                  </div>
                </div>
                <button className="btn-primary mt-4">
                  <span className="truncate">Enroll Now - $199</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Course Grid */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-6 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
            Available Courses
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCourses.map((course, index) => (
              <div key={course.id} className="card float glass-hover" style={{ animationDelay: `${index * 0.1}s` }}>
                <div className="relative mb-4">
                  <div
                    className="w-full h-48 bg-center bg-no-repeat bg-cover rounded-xl"
                    style={{ backgroundImage: `url("${course.thumbnail}")` }}
                  ></div>
                  <div className="absolute top-2 right-2">
                    <span className="px-3 py-1 rounded-full text-xs font-bold transition-colors duration-300" style={{ backgroundColor: 'var(--glass-bg)', color: 'var(--text-primary)' }}>
                      {course.price}
                    </span>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                    {course.title}
                  </h3>
                  <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                    {course.description}
                  </p>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" style={{ color: 'var(--text-secondary)' }} />
                        <span className="text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                          {course.duration}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="h-3 w-3" style={{ color: '#ffaa00' }} />
                        <span className="text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                          {course.rating}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="h-3 w-3" style={{ color: 'var(--text-secondary)' }} />
                      <span className="text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                        {course.students}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                      by {course.instructor}
                    </span>
                    <button className="btn-secondary text-xs">
                      <span className="truncate">Learn More</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Learning Paths */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-6 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
            Learning Paths
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card float" style={{ animationDelay: '0.1s' }}>
              <div className="flex items-center gap-4 mb-4">
                <div className="rounded-xl p-3" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                  <BookOpen className="h-6 w-6" style={{ color: 'var(--accent-color)' }} />
                </div>
                <div>
                  <h3 className="text-lg font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                    Beginner Path
                  </h3>
                  <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                    5 courses • 15 hours
                  </p>
                </div>
              </div>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Start your trading journey with fundamentals, risk management, and basic strategies.
              </p>
            </div>

            <div className="card float" style={{ animationDelay: '0.2s' }}>
              <div className="flex items-center gap-4 mb-4">
                <div className="rounded-xl p-3" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                  <Video className="h-6 w-6" style={{ color: 'var(--accent-color)' }} />
                </div>
                <div>
                  <h3 className="text-lg font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                    Advanced Path
                  </h3>
                  <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                    8 courses • 25 hours
                  </p>
                </div>
              </div>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Master advanced techniques, portfolio management, and sophisticated strategies.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 