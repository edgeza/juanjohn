'use client';

export default function CSSTestPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">CSS Test Page</h1>
        
        {/* Basic Tailwind Classes */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">Basic Tailwind CSS</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-500 text-white p-4 rounded-lg">Blue Box</div>
            <div className="bg-green-500 text-white p-4 rounded-lg">Green Box</div>
            <div className="bg-red-500 text-white p-4 rounded-lg">Red Box</div>
          </div>
        </div>

        {/* Custom Button Classes */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">Custom Button Classes</h2>
          <div className="space-x-4">
            <button className="btn btn-primary">Primary Button</button>
            <button className="btn btn-secondary">Secondary Button</button>
            <button className="btn btn-success">Success Button</button>
            <button className="btn btn-danger">Danger Button</button>
          </div>
        </div>

        {/* Trading Colors */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">Trading Colors</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-bull text-white p-4 rounded-lg text-center">
              Bull Market (Green)
            </div>
            <div className="bg-bear text-white p-4 rounded-lg text-center">
              Bear Market (Red)
            </div>
          </div>
        </div>

        {/* Custom Animations */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">Custom Animations</h2>
          <div className="space-y-4">
            <div className="bg-primary-500 text-white p-4 rounded-lg animate-fade-in">
              Fade In Animation
            </div>
            <div className="bg-success-500 text-white p-4 rounded-lg animate-slide-up">
              Slide Up Animation
            </div>
            <div className="bg-danger-500 text-white p-4 rounded-lg animate-pulse-slow">
              Slow Pulse Animation
            </div>
          </div>
        </div>

        {/* Form Elements */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">Form Elements</h2>
          <div className="space-y-4">
            <div>
              <label className="label">Test Input</label>
              <input 
                type="text" 
                className="input" 
                placeholder="Enter some text..."
              />
            </div>
            <div>
              <label className="label">Test Select</label>
              <select className="input">
                <option>Option 1</option>
                <option>Option 2</option>
                <option>Option 3</option>
              </select>
            </div>
          </div>
        </div>

        {/* Responsive Grid */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">Responsive Grid</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((num) => (
              <div 
                key={num}
                className="bg-gradient-to-br from-primary-400 to-primary-600 text-white p-4 rounded-lg text-center"
              >
                Grid Item {num}
              </div>
            ))}
          </div>
        </div>

        {/* Status Indicator */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">Status</h2>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-green-600 font-medium">CSS is working correctly!</span>
          </div>
        </div>
      </div>
    </div>
  );
}
