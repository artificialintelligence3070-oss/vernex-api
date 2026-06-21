import React, { useState, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sphere, MeshDistortMaterial, Stars } from '@react-three/drei';
import axios from 'axios';

// 3D Animated Core Object
function AnimatedSphere() {
  const sphereRef = useRef();

  useFrame((state) => {
    const clock = state.clock;
    sphereRef.current.rotation.x = clock.getElapsedTime() * 0.3;
    sphereRef.current.rotation.y = clock.getElapsedTime() * 0.4;
  });

  return (
    <Sphere ref={sphereRef} args={[1, 64, 64]} scale={2}>
      <MeshDistortMaterial
        color="#00ffcc"
        attach="material"
        distort={0.4}
        speed={2}
        roughness={0.2}
        metalness={0.8}
        wireframe
      />
    </Sphere>
  );
}

export default function Home() {
  const [myKey, setMyKey] = useState('user-alpha-123'); // Default mock key
  const [phoneNum, setPhoneNum] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleLookup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.get(`/api/lookup?my_key=${myKey}&num=${phoneNum}`);
      setResult(res.data);
    } catch (err) {
      setResult(err.response?.data || { error: "Something went wrong" });
    }
    setLoading(false);
  };

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative', background: '#05050a', overflow: 'hidden', fontFamily: 'sans-serif', color: '#fff' }}>
      
      {/* BACKGROUND 3D CANVAS */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 1 }}>
        <Canvas camera={{ position: [0, 0, 5] }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} intensity={1.5} />
          <AnimatedSphere />
          <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
          <OrbitControls enableZoom={false} />
        </Canvas>
      </div>

      {/* FOREGROUND HTML HUD INTERFACE */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        zIndex: 2,
        width: '90%',
        maxWidth: '500px',
        background: 'rgba(10, 10, 20, 0.75)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(0, 255, 204, 0.2)',
        borderRadius: '16px',
        padding: '30px',
        boxShadow: '0 0 30px rgba(0, 255, 204, 0.1)'
      }}>
        <h1 style={{ margin: '0 0 10px 0', fontSize: '24px', textAlign: 'center', color: '#00ffcc', letterSpacing: '2px' }}>
          CYBER OSINT HUB
        </h1>
        <p style={{ fontSize: '12px', textAlign: 'center', color: '#8a8ab0', marginBottom: '20px' }}>
          Custom Gateway API Manager
        </p>

        <form onSubmit={handleLookup} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <div>
            <label style={{ fontSize: '11px', textTransform: 'uppercase', color: '#00ffcc', display: 'block', marginBottom: '5px' }}>Your Custom API Key</label>
            <input 
              type="text" 
              value={myKey} 
              onChange={(e) => setMyKey(e.target.value)} 
              placeholder="Enter your custom client key"
              style={{ width: '100%', padding: '12px', background: 'rgba(255,255,255,0.05)', border: '1px solid #333', borderRadius: '6px', color: '#fff', outline: 'none' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '11px', textTransform: 'uppercase', color: '#00ffcc', display: 'block', marginBottom: '5px' }}>Target Phone Number</label>
            <input 
              type="text" 
              value={phoneNum} 
              onChange={(e) => setPhoneNum(e.target.value)} 
              placeholder="e.g. 9876543210"
              required
              style={{ width: '100%', padding: '12px', background: 'rgba(255,255,255,0.05)', border: '1px solid #333', borderRadius: '6px', color: '#fff', outline: 'none' }}
            />
          </div>

          <button 
            type="submit" 
            disabled={loading}
            style={{ 
              width: '100%', 
              padding: '14px', 
              background: '#00ffcc', 
              color: '#000', 
              fontWeight: 'bold', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: 'pointer',
              transition: '0.3s',
              boxShadow: '0 4px 15px rgba(0, 255, 204, 0.3)'
            }}
          >
            {loading ? "DECRYPTING ENGINE..." : "EXECUTE REQUEST"}
          </button>
        </form>

        {/* RESULTS DISPLAYER */}
        {result && (
          <div style={{ marginTop: '20px', maxHeight: '220px', overflowY: 'auto', background: 'rgba(0,0,0,0.4)', borderRadius: '6px', padding: '15px', border: '1px solid rgba(255,255,255,0.1)', fontSize: '13px' }}>
            <h3 style={{ margin: '0 0 10px 0', color: result.error ? '#ff4a4a' : '#00ffcc', fontSize: '14px' }}>
              {result.error ? "Execution Failed" : "Data Received"}
            </h3>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontFamily: 'monospace', color: '#b9b9df' }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
