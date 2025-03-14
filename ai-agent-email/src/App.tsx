import React, { useState, useEffect } from 'react';

// Function to generate UUID
const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0, 
          v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

// Define the email details interface
interface EmailDetails {
  status: string;
  current_request: string;
  current_request_draft: string;
  response_id: string;
  email_recipient: string;
  email_subject: string;
  email_body: string;
  send_time_seconds: string;
}

const App: React.FC = () => {
  const [workflowId, setWorkflowId] = useState<string>('');
  const [userInput, setUserInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [emailDetails, setEmailDetails] = useState<EmailDetails | null>(null);

  useEffect(() => {
    // Check for workflowId in URL parameters on component mount
    const urlParams = new URLSearchParams(window.location.search);
    const workflowIdParam = urlParams.get('workflowId');
    
    if (workflowIdParam) {
      setWorkflowId(workflowIdParam);
    }
  }, []);

  // Effect to fetch workflow details when workflowId is available
  useEffect(() => {
    if (workflowId) {
      fetchWorkflowDetails();

      // Set up polling every 3 seconds
      const intervalId = setInterval(fetchWorkflowDetails, 3000);
      
      // Clean up interval on unmount
      return () => clearInterval(intervalId);
    }
  }, [workflowId]);

  const fetchWorkflowDetails = async () => {
    try {
      const res = await fetch(`/api/ai-agent/describe?workflowId=${workflowId}`);
      if (res.ok) {
        // Try to parse as JSON first
        const text = await res.text();
        try {
          const data = JSON.parse(text);
          console.log('Email details fetched:', data);
          setEmailDetails(data);
        } catch (parseError) {
          // If it's not valid JSON, use the text response
          console.error('Error parsing JSON response:', parseError);
          console.log('Raw response:', text);
        }
      } else {
        console.error('Failed to fetch workflow details:', await res.text());
      }
    } catch (error) {
      console.error('Error fetching workflow details:', error);
    }
  };

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
      if (!res.ok) {
        console.error('Failed to send request:', await res.text());
      }
      setUserInput(''); // Clear input after sending
      
      // Fetch updated details after sending a request
      fetchWorkflowDetails();
    } catch (error) {
      console.error('Error sending request:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Render the UI based on whether we have a workflowId
  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>AI Agent for Email</h1>
      
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
        // Show the chat interface and email details if workflowId is present
        <div style={{ display: 'flex', gap: '30px' }}>
          {/* Left side - Chat interface */}
          <div style={{ flex: '1' }}>
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
              
              {emailDetails && emailDetails.status === 'waiting' && (
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
              )}
              
              {emailDetails && (
                <div style={{ 
                  textAlign: 'center',
                  marginTop: '15px'
                }}>
                  <span style={{ 
                    padding: '5px 15px', 
                    borderRadius: '12px', 
                    fontSize: '14px', 
                    fontWeight: 'bold',
                    backgroundColor: emailDetails.status === 'waiting' ? '#4caf50' : '#ff9800',
                    color: 'white',
                    display: 'inline-block'
                  }}>
                    Status: {emailDetails.status}
                  </span>
                </div>
              )}
              
              {/* Add "Start New Email" button when email has been sent */}
              {emailDetails && emailDetails.status === 'sent' && (
                <div style={{ 
                  textAlign: 'center',
                  marginTop: '30px'
                }}>
                  <button
                    onClick={() => window.location.href = window.location.pathname}
                    style={{
                      padding: '10px 20px',
                      backgroundColor: '#4285f4',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontWeight: 'bold',
                      fontSize: '14px'
                    }}
                  >
                    Start New Email
                  </button>
                </div>
              )}
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
          </div>
          
          {/* Right side - Email details */}
          <div style={{ flex: '1' }}>
            <div style={{ 
              border: '1px solid #ddd', 
              borderRadius: '4px',
              backgroundColor: 'white',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              padding: '20px',
              height: '100%'
            }}>
              <h2 style={{ marginTop: '0', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
                Email Draft
              </h2>
              
              {emailDetails ? (
                <div>
                  <div style={{ marginBottom: '15px' }}>
                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
                      To:
                    </label>
                    <div style={{ 
                      padding: '8px', 
                      backgroundColor: '#f5f5f5', 
                      border: '1px solid #ddd',
                      borderRadius: '4px'
                    }}>
                      {emailDetails.email_recipient || 'Not specified yet'}
                    </div>
                  </div>
                  
                  <div style={{ marginBottom: '15px' }}>
                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
                      Subject:
                    </label>
                    <div style={{ 
                      padding: '8px', 
                      backgroundColor: '#f5f5f5', 
                      border: '1px solid #ddd',
                      borderRadius: '4px'
                    }}>
                      {emailDetails.email_subject || 'Not specified yet'}
                    </div>
                  </div>
                  
                  <div style={{ marginBottom: '15px' }}>
                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
                      Body:
                    </label>
                    <div style={{ 
                      padding: '12px',
                      minHeight: '200px',
                      backgroundColor: '#f5f5f5', 
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {emailDetails.email_body || 'Email body will appear here...'}
                    </div>
                  </div>
                  
                  <div>
                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
                      Sending Time:
                    </label>
                    <div style={{ 
                      padding: '8px', 
                      backgroundColor: '#f5f5f5', 
                      border: '1px solid #ddd',
                      borderRadius: '4px'
                    }}>
                      {emailDetails.send_time_seconds ? 
                        new Date(parseInt(emailDetails.send_time_seconds) * 1000).toLocaleString() : 
                        'Not scheduled yet'}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 0', color: '#666' }}>
                  Loading email details...
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;