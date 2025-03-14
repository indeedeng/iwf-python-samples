import React, { useState, useEffect } from 'react';

// Function to generate UUID
const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0, 
          v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

const App: React.FC = () => {
  const [workflowId, setWorkflowId] = useState<string>('');
  const [userInput, setUserInput] = useState<string>('');
  const [response, setResponse] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    // Check for workflowId in URL parameters on component mount
    const urlParams = new URLSearchParams(window.location.search);
    const workflowIdParam = urlParams.get('workflowId');
    
    if (workflowIdParam) {
      setWorkflowId(workflowIdParam);
    }
  }, []);

  const startWorkflow = async () => {
    setIsLoading(true);
    try {
      // Generate a UUID for the workflow
      const newWorkflowId = generateUUID();
      
      // Start the workflow
      const res = await fetch(`/api/ai-agent/start?workflowId=${newWorkflowId}`);
      
      if (res.ok) {
        // Redirect to the same page but with the workflowId as a parameter
        window.location.href = `${window.location.pathname}?workflowId=${newWorkflowId}`;
      } else {
        console.error('Failed to start workflow:', await res.text());
      }
    } catch (error) {
      console.error('Error starting workflow:', error);
      setIsLoading(false);
    }
  };

  const sendRequest = async () => {
    if (!userInput.trim() || !workflowId) return;
    
    setIsLoading(true);
    try {      
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

  // Render the UI based on whether we have a workflowId
  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>AI Agent Email</h1>
      
      {!workflowId ? (
        // Show only the start button if no workflowId is present
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center',
          justifyContent: 'center',
          height: '50vh'
        }}>
          <button 
            onClick={startWorkflow}
            disabled={isLoading}
            style={{
              padding: '20px 40px',
              fontSize: '24px',
              backgroundColor: '#4285f4',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: 'bold',
              boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
            }}
          >
            Start
          </button>
          {isLoading && <p style={{ marginTop: '20px' }}>Starting workflow...</p>}
        </div>
      ) : (
        // Show the chat interface if workflowId is present
        <div>
          <div style={{ marginBottom: '20px' }}>
            <label htmlFor="workflowId">Workflow ID: </label>
            <span 
              id="workflowId"
              style={{ 
                display: 'inline-block',
                padding: '8px',
                backgroundColor: '#f5f5f5',
                border: '1px solid #ddd',
                borderRadius: '4px',
                marginLeft: '5px',
                fontFamily: 'monospace'
              }}
            >
              {workflowId}
            </span>
          </div>
          
          <div>
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Enter your request here..."
              rows={5}
              style={{ 
                width: '100%', 
                padding: '12px', 
                marginBottom: '15px',
                borderRadius: '4px',
                border: '1px solid #ddd',
                fontSize: '16px'
              }}
            />
            
            <button 
              onClick={sendRequest}
              disabled={isLoading || !userInput.trim()}
              style={{
                padding: '12px 24px',
                backgroundColor: '#4285f4',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '16px',
                width: '100%'
              }}
            >
              Talk to Agent
            </button>
          </div>
          
          {isLoading && 
            <div style={{ 
              textAlign: 'center', 
              margin: '20px 0',
              color: '#666'
            }}>
              Processing your request...
            </div>
          }
          
          {response && (
            <div style={{ marginTop: '30px' }}>
              <h2>Response:</h2>
              <div style={{ 
                border: '1px solid #ddd', 
                padding: '20px',
                borderRadius: '4px',
                backgroundColor: '#f9f9f9',
                boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                whiteSpace: 'pre-wrap'
              }}>
                {response}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default App;