import React, { useState } from 'react';
import { useKeycloak } from '@react-keycloak/web';

interface Report {
  id: string;
  date: string;
  patient_name: string;
  doctor_name: string;
  type_of_prosthesis: string;
  status: string;
}

const ReportPage: React.FC = () => {
  const { keycloak, initialized } = useKeycloak();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<Report | null>(null);

  const downloadReport = async () => {
    if (!keycloak?.token) {
      setError('Not authenticated');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setReport(null);

      const response = await fetch(`/api/reports`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${keycloak.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate report');
      }

      const reportData = await response.json();
      setReport(reportData);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (!initialized) {
    return <div>Loading...</div>;
  }

  if (!keycloak.authenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
        <button
          onClick={() => keycloak.login()}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Login
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="w-full max-w-2xl p-8 bg-white rounded-lg shadow-md">
        <h1 className="text-2xl font-bold mb-6">Usage Reports</h1>
        
        <button
          onClick={downloadReport}
          disabled={loading}
          className={`px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 ${
            loading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {loading ? 'Generating Report...' : 'Download Report'}
        </button>

        {error && (
          <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        {report && (
          <div className="mt-6 border rounded-lg p-6 bg-gray-50">
            <h2 className="text-xl font-semibold mb-4">Report Details</h2>
            <div className="grid grid-cols-1 gap-4">
              <div className="flex justify-between border-b pb-2">
                <span className="font-medium">Report ID:</span>
                <span>{report.id}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="font-medium">Date:</span>
                <span>{report.date}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="font-medium">Patient Name:</span>
                <span>{report.patient_name}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="font-medium">Doctor Name:</span>
                <span>{report.doctor_name}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="font-medium">Type of Prosthesis:</span>
                <span>{report.type_of_prosthesis}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="font-medium">Status:</span>
                <span className="capitalize">{report.status}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPage;