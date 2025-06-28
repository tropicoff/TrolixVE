import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const App = () => {
  const [sandboxes, setSandboxes] = useState([]);
  const [activeSandbox, setActiveSandbox] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [osTemplates, setOsTemplates] = useState({});
  const [terminalHistory, setTerminalHistory] = useState([]);
  const [currentCommand, setCurrentCommand] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [showTerminal, setShowTerminal] = useState(false);
  const terminalRef = useRef(null);

  const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchOsTemplates();
    fetchSandboxes();
    
    // Matrix animation setup
    const canvas = document.getElementById('matrix-bg');
    if (canvas) {
      const ctx = canvas.getContext('2d');
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      
      const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?';
      const columns = Math.floor(canvas.width / 10);
      const drops = Array(columns).fill(1);
      
      const drawMatrix = () => {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#00ff41';
        ctx.font = '10px monospace';
        
        for (let i = 0; i < drops.length; i++) {
          const text = chars[Math.floor(Math.random() * chars.length)];
          ctx.fillText(text, i * 10, drops[i] * 10);
          
          if (drops[i] * 10 > canvas.height && Math.random() > 0.975) {
            drops[i] = 0;
          }
          drops[i]++;
        }
      };
      
      const matrixInterval = setInterval(drawMatrix, 50);
      return () => clearInterval(matrixInterval);
    }
  }, []);

  const fetchOsTemplates = async () => {
    try {
      const response = await fetch(`${API_URL}/api/os-templates`);
      const data = await response.json();
      setOsTemplates(data);
    } catch (error) {
      console.error('Error fetching OS templates:', error);
    }
  };

  const fetchSandboxes = async () => {
    try {
      const response = await fetch(`${API_URL}/api/sandboxes`);
      const data = await response.json();
      setSandboxes(data);
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching sandboxes:', error);
      setIsLoading(false);
    }
  };

  const createSandbox = async (config) => {
    try {
      const response = await fetch(`${API_URL}/api/sandboxes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        fetchSandboxes();
        setShowCreateModal(false);
      }
    } catch (error) {
      console.error('Error creating sandbox:', error);
    }
  };

  const controlSandbox = async (sandboxId, action) => {
    try {
      const response = await fetch(`${API_URL}/api/sandboxes/${sandboxId}/${action}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        fetchSandboxes();
      }
    } catch (error) {
      console.error(`Error ${action} sandbox:`, error);
    }
  };

  const deleteSandbox = async (sandboxId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cette sandbox ?')) {
      try {
        const response = await fetch(`${API_URL}/api/sandboxes/${sandboxId}`, {
          method: 'DELETE'
        });
        
        if (response.ok) {
          fetchSandboxes();
          if (activeSandbox?.id === sandboxId) {
            setActiveSandbox(null);
            setShowTerminal(false);
          }
        }
      } catch (error) {
        console.error('Error deleting sandbox:', error);
      }
    }
  };

  const openTerminal = async (sandbox) => {
    setActiveSandbox(sandbox);
    setShowTerminal(true);
    
    // Fetch terminal history
    try {
      const response = await fetch(`${API_URL}/api/terminal/${sandbox.id}/history`);
      const history = await response.json();
      setTerminalHistory(history);
    } catch (error) {
      console.error('Error fetching terminal history:', error);
    }
  };

  const executeCommand = async (command) => {
    if (!activeSandbox || !command.trim()) return;
    
    try {
      const response = await fetch(`${API_URL}/api/terminal/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sandbox_id: activeSandbox.id,
          command: command
        })
      });
      
      const result = await response.json();
      
      setTerminalHistory(prev => [...prev, {
        command: result.command,
        output: result.output,
        timestamp: result.timestamp
      }]);
      
      setCurrentCommand('');
    } catch (error) {
      console.error('Error executing command:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      executeCommand(currentCommand);
    }
  };

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [terminalHistory]);

  const CreateSandboxModal = () => {
    const [config, setConfig] = useState({
      name: '',
      os_type: 'kali',
      cpu_cores: 2,
      ram_gb: 4,
      disk_gb: 20,
      network_isolated: true
    });

    return (
      <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
        <div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <h2>🚀 Nouvelle Sandbox</h2>
            <button onClick={() => setShowCreateModal(false)}>✕</button>
          </div>
          
          <div className="modal-body">
            <div className="form-group">
              <label>Nom de la Sandbox</label>
              <input
                type="text"
                value={config.name}
                onChange={(e) => setConfig({...config, name: e.target.value})}
                placeholder="Ex: Penetration-Test-Lab"
              />
            </div>

            <div className="form-group">
              <label>Système d'Exploitation</label>
              <div className="os-grid">
                {Object.entries(osTemplates).map(([key, os]) => (
                  <div
                    key={key}
                    className={`os-option ${config.os_type === key ? 'selected' : ''}`}
                    onClick={() => setConfig({...config, os_type: key})}
                  >
                    <span className="os-icon">{os.icon}</span>
                    <span className="os-name">{os.name}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>CPU Cores</label>
                <select value={config.cpu_cores} onChange={(e) => setConfig({...config, cpu_cores: parseInt(e.target.value)})}>
                  <option value={1}>1 Core</option>
                  <option value={2}>2 Cores</option>
                  <option value={4}>4 Cores</option>
                  <option value={8}>8 Cores</option>
                </select>
              </div>

              <div className="form-group">
                <label>RAM (GB)</label>
                <select value={config.ram_gb} onChange={(e) => setConfig({...config, ram_gb: parseInt(e.target.value)})}>
                  <option value={2}>2 GB</option>
                  <option value={4}>4 GB</option>
                  <option value={8}>8 GB</option>
                  <option value={16}>16 GB</option>
                </select>
              </div>

              <div className="form-group">
                <label>Stockage (GB)</label>
                <select value={config.disk_gb} onChange={(e) => setConfig({...config, disk_gb: parseInt(e.target.value)})}>
                  <option value={20}>20 GB</option>
                  <option value={50}>50 GB</option>
                  <option value={100}>100 GB</option>
                  <option value={200}>200 GB</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={config.network_isolated}
                  onChange={(e) => setConfig({...config, network_isolated: e.target.checked})}
                />
                Réseau Isolé (Sécurisé)
              </label>
            </div>
          </div>

          <div className="modal-footer">
            <button className="btn-secondary" onClick={() => setShowCreateModal(false)}>
              Annuler
            </button>
            <button 
              className="btn-primary" 
              onClick={() => createSandbox(config)}
              disabled={!config.name}
            >
              Créer Sandbox
            </button>
          </div>
        </div>
      </div>
    );
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return '#00ff41';
      case 'stopped': return '#ff4444';
      case 'saved': return '#ffaa00';
      case 'creating': return '#0099ff';
      default: return '#666';
    }
  };

  if (isLoading) {
    return (
      <div className="loading-screen">
        <canvas id="matrix-bg"></canvas>
        <div className="loading-content">
          <div className="logo">TrolixVE</div>
          <div className="loading-text">Initialisation des systèmes...</div>
          <div className="loading-spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <canvas id="matrix-bg"></canvas>
      
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-text">TrolixVE</span>
            <span className="logo-subtitle">Multi-Sandbox OS Manager</span>
          </div>
          <div className="header-stats">
            <div className="stat">
              <span className="stat-label">Sandboxes Actives</span>
              <span className="stat-value">{sandboxes.filter(s => s.status === 'running').length}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Total</span>
              <span className="stat-value">{sandboxes.length}</span>
            </div>
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="toolbar">
          <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
            ➕ Nouvelle Sandbox
          </button>
          <button className="btn-secondary" onClick={fetchSandboxes}>
            🔄 Actualiser
          </button>
        </div>

        <div className="sandboxes-grid">
          {sandboxes.map(sandbox => (
            <div key={sandbox.id} className="sandbox-card">
              <div className="sandbox-header">
                <div className="sandbox-info">
                  <h3>{sandbox.name}</h3>
                  <span className="os-badge">
                    {osTemplates[sandbox.os_type]?.icon} {osTemplates[sandbox.os_type]?.name}
                  </span>
                </div>
                <div 
                  className="status-indicator"
                  style={{ backgroundColor: getStatusColor(sandbox.status) }}
                >
                  {sandbox.status}
                </div>
              </div>

              <div className="sandbox-specs">
                <div className="spec">🖥️ {sandbox.cpu_cores} Cores</div>
                <div className="spec">💾 {sandbox.ram_gb} GB RAM</div>
                <div className="spec">💿 {sandbox.disk_gb} GB Disque</div>
                <div className="spec">
                  {sandbox.network_isolated ? '🔒 Isolé' : '🌐 Réseau'}
                </div>
              </div>

              <div className="sandbox-actions">
                {sandbox.status === 'stopped' && (
                  <button 
                    className="btn-success"
                    onClick={() => controlSandbox(sandbox.id, 'start')}
                  >
                    ▶️ Démarrer
                  </button>
                )}
                
                {sandbox.status === 'running' && (
                  <>
                    <button 
                      className="btn-primary"
                      onClick={() => openTerminal(sandbox)}
                    >
                      💻 Terminal
                    </button>
                    <button 
                      className="btn-warning"
                      onClick={() => controlSandbox(sandbox.id, 'stop')}
                    >
                      ⏹️ Arrêter
                    </button>
                  </>
                )}

                <button 
                  className="btn-info"
                  onClick={() => controlSandbox(sandbox.id, 'save')}
                >
                  💾 Sauver
                </button>
                
                <button 
                  className="btn-danger"
                  onClick={() => deleteSandbox(sandbox.id)}
                >
                  🗑️ Supprimer
                </button>
              </div>

              <div className="sandbox-footer">
                <small>Créé: {new Date(sandbox.created_at).toLocaleDateString()}</small>
              </div>
            </div>
          ))}
        </div>

        {sandboxes.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">🚀</div>
            <h3>Aucune Sandbox</h3>
            <p>Créez votre première sandbox pour commencer vos tests de sécurité</p>
            <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
              Créer une Sandbox
            </button>
          </div>
        )}
      </main>

      {showTerminal && activeSandbox && (
        <div className="terminal-overlay" onClick={() => setShowTerminal(false)}>
          <div className="terminal-window" onClick={e => e.stopPropagation()}>
            <div className="terminal-header">
              <div className="terminal-title">
                <span>🖥️ {activeSandbox.name} - {osTemplates[activeSandbox.os_type]?.name}</span>
              </div>
              <button onClick={() => setShowTerminal(false)}>✕</button>
            </div>
            
            <div className="terminal-body" ref={terminalRef}>
              <div className="terminal-welcome">
                Bienvenue dans TrolixVE Terminal
                <br />Sandbox: {activeSandbox.name}
                <br />OS: {osTemplates[activeSandbox.os_type]?.name}
                <br />Tapez 'help' pour voir les commandes disponibles
                <br />
              </div>
              
              {terminalHistory.map((entry, index) => (
                <div key={index} className="terminal-entry">
                  <div className="terminal-prompt">
                    <span className="prompt-user">root@{activeSandbox.name.toLowerCase()}</span>
                    <span className="prompt-path">:~#</span>
                    <span className="prompt-command">{entry.command}</span>
                  </div>
                  <div className="terminal-output">{entry.output}</div>
                </div>
              ))}
              
              <div className="terminal-input-line">
                <span className="prompt-user">root@{activeSandbox.name.toLowerCase()}</span>
                <span className="prompt-path">:~#</span>
                <input
                  type="text"
                  value={currentCommand}
                  onChange={(e) => setCurrentCommand(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="terminal-input"
                  autoFocus
                  placeholder="Tapez votre commande..."
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {showCreateModal && <CreateSandboxModal />}
    </div>
  );
};

export default App;