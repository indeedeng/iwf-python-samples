import React, { useState } from 'react';

const App: React.FC = () => {
  const [workflowId, setWorkflowId] = useState<string>('test'); // Default workflow ID
  const [userInput, setUserInput] = useState<string>('');
  const [response, setResponse] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [workflowStarted, setWorkflowStarted] = useState<boolean>(false);

  const startWorkflow = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`/api/ai-agent/start?workflowId=${workflowId}`);
      if (res.ok) {
        setWorkflowStarted(true);
      }
    } catch (error) {
      console.error('Error starting workflow:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const sendRequest = async () => {
    if (!userInput.trim()) return;
    
    setIsLoading(true);
    try {
      // Start workflow if not already started
      if (!workflowStarted) {
        await startWorkflow();
      }
      
      const encodedRequest = encodeURIComponent(userInput);
      const res = await fetch(`/api/ai-agent/request?workflowId=${workflowId}&request=${encodedRequest}`);
      const data = await res.text();
      setResponse(data);
    } catch (error) {
      console.error('Error sending request:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>AI Agent Email</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="workflowId">Workflow ID: </label>
        <input
          type="text"
          id="workflowId"
          value={workflowId}
          onChange={(e) => setWorkflowId(e.target.value)}
          style={{ marginLeft: '5px' }}
        />
        {!workflowStarted && (
          <button 
            onClick={startWorkflow} 
            disabled={isLoading}
            style={{ marginLeft: '10px' }}
          >
            Start Workflow
          </button>
        )}
      </div>
      
      <div>
        <textarea
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          placeholder="Enter your request here..."
          rows={5}
          style={{ width: '100%', padding: '10px', marginBottom: '10px' }}
        />
        
        <button 
          onClick={sendRequest}
          disabled={isLoading || !userInput.trim()}
          style={{
            padding: '10px 20px',
            backgroundColor: '#4285f4',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          Talk to Agent
        </button>
      </div>
      
      {isLoading && <p>Processing...</p>}
      
      {response && (
        <div style={{ marginTop: '20px' }}>
          <h2>Response:</h2>
          <div style={{ 
            border: '1px solid #ddd', 
            padding: '15px',
            borderRadius: '4px',
            backgroundColor: '#f9f9f9' 
          }}>
            {response}
          </div>
        </div>
      )}
    </div>
  );
};

export default App;