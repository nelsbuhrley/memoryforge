import { useEffect, useState } from 'react'
import { getSubjects, uploadMaterial, getMaterials, parseNow, parseMaterials } from '../api/client'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'
import Badge from '../components/ui/Badge'

const STATUS_COLOR = {
  pending: 'slate',
  processing: 'yellow',
  complete: 'green',
  error: 'red',
}

export default function Upload() {
  const [subjects, setSubjects] = useState([])
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedSubject, setSelectedSubject] = useState('')
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [parsing, setParsing] = useState({}) // { [materialId]: true }
  const [parseAllRunning, setParseAllRunning] = useState(false)
  const [parseAllResult, setParseAllResult] = useState(null)

  const load = async () => {
    const [s, m] = await Promise.all([getSubjects(), getMaterials()])
    setSubjects(s)
    setMaterials(m)
    if (s.length && !selectedSubject) setSelectedSubject(String(s[0].id))
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const handleUpload = async () => {
    if (!file || !selectedSubject) return
    setUploading(true)
    setUploadError(null)
    try {
      const fd = new FormData()
      fd.append('subject_id', selectedSubject)
      fd.append('file', file)
      await uploadMaterial(fd)
      setFile(null)
      await load()
    } catch (e) {
      setUploadError(e.message)
    } finally {
      setUploading(false)
    }
  }

  const handleParseNow = async (id) => {
    setParsing((p) => ({ ...p, [id]: true }))
    try {
      await parseNow(id)
    } catch (e) {
      // error visible via status badge after reload
    } finally {
      setParsing((p) => ({ ...p, [id]: false }))
      await load()
    }
  }

  const handleParseAll = async (force = false) => {
    setParseAllRunning(true)
    setParseAllResult(null)
    try {
      const result = await parseMaterials(force)
      setParseAllResult(result)
      await load()
    } catch (e) {
      setParseAllResult({ error: e.message })
    } finally {
      setParseAllRunning(false)
    }
  }

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>

  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold text-slate-100">Upload Material</h1>

      <Card className="space-y-4">
        <div>
          <label className="block text-sm text-slate-400 mb-1">Subject</label>
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-slate-100 text-sm"
          >
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm text-slate-400 mb-1">File</label>
          <input
            data-testid="file-input"
            type="file"
            accept=".pdf,.txt,.md,.docx"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-forge-600 file:text-white file:text-sm file:font-medium file:cursor-pointer hover:file:bg-forge-500 file:transition-colors cursor-pointer"
          />
          {file && <p className="text-slate-500 text-xs mt-1">{file.name} ({(file.size / 1024).toFixed(1)} KB)</p>}
        </div>

        {uploadError && <p className="text-red-400 text-sm">{uploadError}</p>}

        <Button
          onClick={handleUpload}
          disabled={!file || !selectedSubject || uploading}
        >
          {uploading ? <><Spinner size="sm" /> Uploading...</> : 'Upload'}
        </Button>
      </Card>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-slate-200">Uploaded Materials</h2>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={() => handleParseAll(false)} disabled={parseAllRunning} title="Parse any pending/unprocessed materials">
              {parseAllRunning ? <><Spinner size="sm" /> Parsing...</> : 'Parse Pending'}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => handleParseAll(true)} disabled={parseAllRunning} title="Force re-parse all materials including complete ones with 0 KUs">
              Force Parse All
            </Button>
          </div>
        </div>
        {parseAllResult && (
          <div className={`mb-3 p-3 rounded-lg text-sm ${parseAllResult.error ? 'bg-red-900/40 text-red-300' : 'bg-slate-800 text-slate-300'}`}>
            {parseAllResult.error
              ? `Error: ${parseAllResult.error}`
              : `Parsed ${parseAllResult.processed} material(s). ${parseAllResult.details?.map(d => `${d.filename}: ${d.ku_count} KUs`).join(', ')}`
            }
          </div>
        )}
        <div className="space-y-2">
          {materials.length === 0 && (
            <p className="text-slate-500">No materials uploaded yet.</p>
          )}
          {materials.map((m) => (
            <Card key={m.id} className="flex items-center gap-3">
              <div className="flex-1">
                <p className="text-slate-200 text-sm font-medium">{m.filename}</p>
                <p className="text-slate-500 text-xs">
                  {m.file_type?.toUpperCase()}
                  {m.ku_count != null && m.ku_count > 0 && (
                    <span className="ml-2 text-forge-400">{m.ku_count} knowledge units</span>
                  )}
                </p>
              </div>
              <Badge color={STATUS_COLOR[m.parse_status] ?? 'slate'}>{m.parse_status}</Badge>
              <Button
                size="sm"
                variant={m.parse_status === 'error' ? 'danger' : 'ghost'}
                disabled={!!parsing[m.id]}
                onClick={() => handleParseNow(m.id)}
              >
                {parsing[m.id]
                  ? <><Spinner size="sm" /> Parsing...</>
                  : m.parse_status === 'error' ? 'Retry' : 'Parse Now'}
              </Button>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
