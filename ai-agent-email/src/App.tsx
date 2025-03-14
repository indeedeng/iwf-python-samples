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
  const [isDraftSaving, setIsDraftSaving] = useState<boolean>(false);
  const [lastSavedDraft, setLastSavedDraft] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

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
    // Create separate functions for initial load and refresh
    const fetchWorkflowDetailsInitial = async () => {
      try {
        const res = await fetch(`/api/ai-agent/describe?workflowId=${workflowId}`);
        if (res.ok) {
          // Try to parse as JSON first
          const text = await res.text();
          try {
            const data = JSON.parse(text);
            console.log('Email details fetched (initial):', data);
            setEmailDetails(data);
            
            // Set the draft text from the API if the user hasn't typed anything yet
            // This happens only on initial load
            if (data.current_request_draft && userInput === '') {
              setUserInput(data.current_request_draft);
              setLastSavedDraft(data.current_request_draft);
            }
          } catch (parseError) {
            // If it's not valid JSON, use the text response
            setErrorMessage(`Error parsing JSON response: ${parseError instanceof Error ? parseError.message : String(parseError)}`);
            console.error('Error parsing JSON response:', parseError);
            console.log('Raw response:', text);
          }
        } else {
          const errorText = await res.text();
          setErrorMessage(`Failed to fetch workflow details: ${errorText}`);
          console.error('Failed to fetch workflow details:', errorText);
        }
      } catch (error) {
        setErrorMessage(`Error fetching workflow details: ${error instanceof Error ? error.message : String(error)}`);
        console.error('Error fetching workflow details:', error);
      }
    };
    
    // This function is for refresh only - it doesn't set the draft input
    const fetchWorkflowDetailsRefresh = async () => {
      try {
        const res = await fetch(`/api/ai-agent/describe?workflowId=${workflowId}`);
        if (res.ok) {
          // Try to parse as JSON first
          const text = await res.text();
          try {
            const data = JSON.parse(text);
            console.log('Email details fetched (refresh):', data);
            setEmailDetails(data);
            // Intentionally NOT updating the input box with the draft here
          } catch (parseError) {
            // If it's not valid JSON, use the text response
            setErrorMessage(`Error parsing JSON response: ${parseError instanceof Error ? parseError.message : String(parseError)}`);
            console.error('Error parsing JSON response:', parseError);
            console.log('Raw response:', text);
          }
        } else {
          const errorText = await res.text();
          setErrorMessage(`Failed to fetch workflow details: ${errorText}`);
          console.error('Failed to fetch workflow details:', errorText);
        }
      } catch (error) {
        setErrorMessage(`Error fetching workflow details: ${error instanceof Error ? error.message : String(error)}`);
        console.error('Error fetching workflow details:', error);
      }
    };

    if (workflowId) {
      // Call initial function for the first load
      fetchWorkflowDetailsInitial();

      // Set up polling every 3 seconds with the refresh function
      const intervalId = setInterval(fetchWorkflowDetailsRefresh, 3000);
      
      // Clean up interval on unmount
      return () => clearInterval(intervalId);
    }
  }, [workflowId]);
  
  // Effect to auto-save drafts on a fixed interval (not on every keystroke)
  useEffect(() => {
    let saveInterval: NodeJS.Timeout | null = null;
    
    // Define the save draft function inside the effect to capture the latest state
    const saveDraftInInterval = async () => {
      if (!workflowId || !userInput.trim()) return;
      
      // Only save if the draft has changed 
      if (userInput !== lastSavedDraft) {
        try {
          setIsDraftSaving(true);
          const encodedDraft = encodeURIComponent(userInput);
          const res = await fetch(`/api/ai-agent/save_draft?workflowId=${workflowId}&draft=${encodedDraft}`);
          
          if (res.ok) {
            // Update last saved draft
            setLastSavedDraft(userInput);
            // Clear any previous error messages
            setErrorMessage('');
          } else {
            const errorText = await res.text();
            setErrorMessage(`Failed to save draft: ${errorText}`);
            console.error('Failed to save draft:', errorText);
          }
        } catch (error) {
          setErrorMessage(`Error saving draft: ${error instanceof Error ? error.message : String(error)}`);
          console.error('Error saving draft:', error);
        } finally {
          setIsDraftSaving(false);
        }
      }
    };
    
    if (workflowId) {
      // Set up interval to auto-save every 5 seconds
      saveInterval = setInterval(saveDraftInInterval, 5000);
    }
    
    return () => {
      if (saveInterval) {
        clearInterval(saveInterval);
      }
    };
  }, [workflowId, userInput, lastSavedDraft]);

  // Used only for manual refresh, not interval polling
  const fetchWorkflowDetails = async () => {
    try {
      const res = await fetch(`/api/ai-agent/describe?workflowId=${workflowId}`);
      if (res.ok) {
        // Try to parse as JSON first
        const text = await res.text();
        try {
          const data = JSON.parse(text);
          console.log('Email details fetched (manual):', data);
          setEmailDetails(data);
          
          // We do NOT set the input from the draft here
        } catch (parseError) {
          // If it's not valid JSON, use the text response
          setErrorMessage(`Error parsing JSON response: ${parseError instanceof Error ? parseError.message : String(parseError)}`);
          console.error('Error parsing JSON response:', parseError);
          console.log('Raw response:', text);
        }
      } else {
        const errorText = await res.text();
        setErrorMessage(`Failed to fetch workflow details: ${errorText}`);
        console.error('Failed to fetch workflow details:', errorText);
      }
    } catch (error) {
      setErrorMessage(`Error fetching workflow details: ${error instanceof Error ? error.message : String(error)}`);
      console.error('Error fetching workflow details:', error);
    }
  };

  // Manual draft saving (not used in the current UI)
  const saveDraft = async () => {
    if (!workflowId || !userInput.trim()) return;
    
    // Only save if the draft has changed 
    if (userInput !== lastSavedDraft) {
      try {
        setIsDraftSaving(true);
        const encodedDraft = encodeURIComponent(userInput);
        const res = await fetch(`/api/ai-agent/save_draft?workflowId=${workflowId}&draft=${encodedDraft}`);
        
        if (res.ok) {
          // Update last saved draft
          setLastSavedDraft(userInput);
          // Clear any previous error messages
          setErrorMessage('');
        } else {
          const errorText = await res.text();
          setErrorMessage(`Failed to save draft: ${errorText}`);
          console.error('Failed to save draft:', errorText);
        }
      } catch (error) {
        setErrorMessage(`Error saving draft: ${error instanceof Error ? error.message : String(error)}`);
        console.error('Error saving draft:', error);
      } finally {
        setIsDraftSaving(false);
      }
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
        const errorText = await res.text();
        setErrorMessage(`Failed to start workflow: ${errorText}`);
        console.error('Failed to start workflow:', errorText);
        setIsLoading(false);
      }
    } catch (error) {
      setErrorMessage(`Error starting workflow: ${error instanceof Error ? error.message : String(error)}`);
      console.error('Error starting workflow:', error);
      setIsLoading(false);
    }
  };

  const sendRequest = async () => {
    if (!userInput.trim() || !workflowId) return;
    
    setIsLoading(true);
    try {      
      // Send the request
      const encodedRequest = encodeURIComponent(userInput);
      const res = await fetch(`/api/ai-agent/request?workflowId=${workflowId}&request=${encodedRequest}`);
      if (res.ok) {
        // Clear any previous error messages on success
        setErrorMessage('');
      } else {
        const errorText = await res.text();
        setErrorMessage(`Failed to send request: ${errorText}`);
        console.error('Failed to send request:', errorText);
      }
      
      // Clear input and reset last saved draft after sending
      setUserInput('');
      setLastSavedDraft('');
      
      // Function to fetch workflow details
      const fetchWorkflowDetailsForUpdate = async () => {
        try {
          const res = await fetch(`/api/ai-agent/describe?workflowId=${workflowId}`);
          if (res.ok) {
            const text = await res.text();
            try {
              const data = JSON.parse(text);
              setEmailDetails(data);
              // Clear error on successful fetch
              setErrorMessage('');
              
              // We do NOT update the input box with draft here
              // This keeps the sendRequest behavior consistent with our change
            } catch (parseError) {
              setErrorMessage(`Error parsing JSON response: ${parseError instanceof Error ? parseError.message : String(parseError)}`);
              console.error('Error parsing JSON response:', parseError);
            }
          } else {
            const errorText = await res.text();
            setErrorMessage(`Failed to fetch workflow details: ${errorText}`);
            console.error('Failed to fetch workflow details:', errorText);
          }
        } catch (error) {
          setErrorMessage(`Error fetching workflow details: ${error instanceof Error ? error.message : String(error)}`);
          console.error('Error fetching workflow details:', error);
        }
      };
      
      // Fetch updated details immediately after sending a request
      await fetchWorkflowDetailsForUpdate();
      
      // Set up a series of follow-up calls to get the latest status
      // This helps to capture the state transition more quickly
      setTimeout(() => fetchWorkflowDetailsForUpdate(), 1000);
      setTimeout(() => fetchWorkflowDetailsForUpdate(), 3000);
      setTimeout(() => fetchWorkflowDetailsForUpdate(), 6000);
    } catch (error) {
      setErrorMessage(`Error sending request: ${error instanceof Error ? error.message : String(error)}`);
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
          {errorMessage && (
            <div style={{
              backgroundColor: '#ffebee',
              color: '#d32f2f',
              padding: '8px 16px',
              borderRadius: '4px',
              fontSize: '14px',
              marginTop: '15px',
              textAlign: 'center',
              maxWidth: '400px'
            }}>
              {errorMessage}
            </div>
          )}
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
                placeholder="Enter your request here... (drafts auto-save)"
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
              
              <div style={{ 
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '10px',
                marginTop: '15px'
              }}>
                <div style={{ 
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  gap: '15px'
                }}>
                  {emailDetails && (
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
                  )}
                  
                  {isDraftSaving && (
                    <span style={{ 
                      fontSize: '12px',
                      color: '#666',
                      fontStyle: 'italic'
                    }}>
                      Saving draft...
                    </span>
                  )}
                </div>
                
                {errorMessage && (
                  <div style={{
                    backgroundColor: '#ffebee',
                    color: '#d32f2f',
                    padding: '8px 16px',
                    borderRadius: '4px',
                    fontSize: '14px',
                    width: '100%',
                    textAlign: 'center',
                    marginTop: '5px'
                  }}>
                    {errorMessage}
                  </div>
                )}
              </div>
              
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