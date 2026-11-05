import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, X, BookOpen, Layers, Bookmark, FileText, ArrowRight, Loader2 } from 'lucide-react'
import api from '@/lib/api'
import { useI18n } from '@/i18n/I18nProvider'

interface SearchItem {
  id: string
  category: 'subject' | 'chapter' | 'topic' | 'concept' | 'material'
  title: string
  subtitle: string
  code?: string
  difficulty?: string
  grade?: number
  url: string
}

interface SearchResponse {
  query: string
  total: number
  categories: {
    subjects: SearchItem[]
    chapters: SearchItem[]
    topics: SearchItem[]
    concepts: SearchItem[]
    materials: SearchItem[]
  }
}

interface GlobalSearchModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function GlobalSearchModal({ isOpen, onClose }: GlobalSearchModalProps) {
  const { lang } = useI18n()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState<string>('all')
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50)
      setQuery('')
      setResults(null)
      setSelectedIndex(0)
    }
  }, [isOpen])

  // Debounced search query
  useEffect(() => {
    if (!query.trim()) {
      setResults(null)
      setIsLoading(false)
      return
    }

    const timer = setTimeout(async () => {
      setIsLoading(true)
      try {
        const res = await api.get('/search', {
          params: { q: query.trim(), lang },
        })
        setResults(res.data)
        setSelectedIndex(0)
      } catch (err) {
        console.error('Search error:', err)
      } finally {
        setIsLoading(false)
      }
    }, 250)

    return () => clearTimeout(timer)
  }, [query, lang])

  if (!isOpen) return null

  // Flatten items for filtering & keyboard navigation
  const allItems: SearchItem[] = []
  if (results) {
    if (activeCategory === 'all' || activeCategory === 'subjects') {
      allItems.push(...results.categories.subjects)
    }
    if (activeCategory === 'all' || activeCategory === 'chapters') {
      allItems.push(...results.categories.chapters)
    }
    if (activeCategory === 'all' || activeCategory === 'topics') {
      allItems.push(...results.categories.topics)
    }
    if (activeCategory === 'all' || activeCategory === 'concepts') {
      allItems.push(...results.categories.concepts)
    }
    if (activeCategory === 'all' || activeCategory === 'materials') {
      allItems.push(...results.categories.materials)
    }
  }

  const handleSelect = (url: string) => {
    navigate(url)
    onClose()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose()
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((prev) => (prev + 1 < allItems.length ? prev + 1 : prev))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : 0))
    } else if (e.key === 'Enter' && allItems[selectedIndex]) {
      e.preventDefault()
      handleSelect(allItems[selectedIndex].url)
    }
  }

  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case 'subject':
        return <BookOpen className="w-4 h-4 text-[#000000]" />
      case 'chapter':
        return <Layers className="w-4 h-4 text-[#000000]" />
      case 'topic':
        return <Bookmark className="w-4 h-4 text-[#000000]" />
      case 'concept':
        return <BookOpen className="w-4 h-4 text-[#000000]" />
      case 'material':
        return <FileText className="w-4 h-4 text-[#000000]" />
      default:
        return <Search className="w-4 h-4 text-[#333333]" />
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 px-4 bg-black/40 backdrop-blur-2xs transition-opacity animate-in fade-in">
      <div
        className="w-full max-w-2xl bg-white rounded-lg shadow-xl border border-[#ccd5ae] overflow-hidden flex flex-col max-h-[80vh] text-[#000000]"
        onKeyDown={handleKeyDown}
      >
        {/* Search Input Bar */}
        <div className="relative flex items-center px-4 py-3 border-b border-[#ccd5ae] bg-[#faedcd]/40">
          <Search className="w-4 h-4 text-[#333333] shrink-0 mr-3" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search CBSE subjects, chapters, topics, concepts, formulas…"
            className="w-full bg-transparent text-[#000000] placeholder-[#666666] text-sm focus:outline-none"
          />
          {isLoading ? (
            <Loader2 className="w-4 h-4 text-[#000000] animate-spin shrink-0 ml-2" />
          ) : query ? (
            <button
              onClick={() => setQuery('')}
              className="p-1 text-[#333333] hover:text-[#000000] rounded transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          ) : (
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded border border-[#ccd5ae] text-[#333333] bg-white">
              ESC
            </span>
          )}
        </div>

        {/* Filter Categories Bar */}
        {results && (
          <div className="flex items-center gap-1.5 px-4 py-2 border-b border-[#ccd5ae] bg-[#fefae0] overflow-x-auto text-xs">
            <button
              onClick={() => { setActiveCategory('all'); setSelectedIndex(0); }}
              className={`px-3 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${
                activeCategory === 'all'
                  ? 'bg-[#ccd5ae] text-[#000000] font-bold border border-[#ccd5ae]'
                  : 'text-[#333333] hover:bg-[#e9edc9]'
              }`}
            >
              All ({results.total})
            </button>
            <button
              onClick={() => { setActiveCategory('subjects'); setSelectedIndex(0); }}
              className={`px-3 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${
                activeCategory === 'subjects'
                  ? 'bg-[#ccd5ae] text-[#000000] font-bold border border-[#ccd5ae]'
                  : 'text-[#333333] hover:bg-[#e9edc9]'
              }`}
            >
              Subjects ({results.categories.subjects.length})
            </button>
            <button
              onClick={() => { setActiveCategory('chapters'); setSelectedIndex(0); }}
              className={`px-3 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${
                activeCategory === 'chapters'
                  ? 'bg-[#ccd5ae] text-[#000000] font-bold border border-[#ccd5ae]'
                  : 'text-[#333333] hover:bg-[#e9edc9]'
              }`}
            >
              Chapters ({results.categories.chapters.length})
            </button>
            <button
              onClick={() => { setActiveCategory('topics'); setSelectedIndex(0); }}
              className={`px-3 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${
                activeCategory === 'topics'
                  ? 'bg-[#ccd5ae] text-[#000000] font-bold border border-[#ccd5ae]'
                  : 'text-[#333333] hover:bg-[#e9edc9]'
              }`}
            >
              Topics ({results.categories.topics.length})
            </button>
            <button
              onClick={() => { setActiveCategory('concepts'); setSelectedIndex(0); }}
              className={`px-3 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${
                activeCategory === 'concepts'
                  ? 'bg-[#ccd5ae] text-[#000000] font-bold border border-[#ccd5ae]'
                  : 'text-[#333333] hover:bg-[#e9edc9]'
              }`}
            >
              Concepts ({results.categories.concepts.length})
            </button>
          </div>
        )}

        {/* Results List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1 divide-y divide-[#ccd5ae]/40">
          {!query.trim() ? (
            <div className="py-12 text-center text-[#333333]">
              <Search className="w-8 h-8 mx-auto mb-2 text-[#ccd5ae]" />
              <p className="text-sm font-semibold text-[#000000]">Quick Curriculum Discovery</p>
              <p className="text-xs text-[#333333] mt-1">
                Type topics like "Motion", "Equations", "Chemical Reactions", or "Democracy"
              </p>
            </div>
          ) : isLoading && !results ? (
            <div className="py-12 text-center text-[#333333]">
              <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-[#000000]" />
              <p className="text-xs">Searching NCERT curriculum…</p>
            </div>
          ) : allItems.length === 0 ? (
            <div className="py-12 text-center text-[#333333]">
              <BookOpen className="w-8 h-8 mx-auto mb-2 text-[#ccd5ae]" />
              <p className="text-sm font-semibold text-[#000000]">No matching curriculum content</p>
              <p className="text-xs text-[#333333] mt-1">
                Try searching with broader terms or check chapter keywords.
              </p>
            </div>
          ) : (
            allItems.map((item, index) => {
              const isSelected = index === selectedIndex
              return (
                <div
                  key={`${item.category}-${item.id}-${index}`}
                  onClick={() => handleSelect(item.url)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`flex items-center justify-between p-2.5 rounded-md cursor-pointer transition-colors ${
                    isSelected ? 'bg-[#e9edc9] border border-[#ccd5ae]' : 'hover:bg-[#fefae0]'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-7 h-7 rounded bg-white border border-[#ccd5ae] flex items-center justify-center shrink-0">
                      {getCategoryIcon(item.category)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-[#000000] truncate">
                          {item.title}
                        </span>
                        <span className="text-[10px] font-medium uppercase px-1.5 py-0.2 rounded bg-[#faedcd] text-[#000000] border border-[#ccd5ae] shrink-0">
                          {item.category}
                        </span>
                        {item.difficulty && (
                          <span className="text-[10px] font-medium uppercase px-1.5 py-0.2 rounded bg-[#e9edc9] text-[#000000] border border-[#ccd5ae] shrink-0">
                            {item.difficulty}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-[#333333] truncate mt-0.5">
                        {item.subtitle}
                      </p>
                    </div>
                  </div>

                  <ArrowRight
                    className={`w-3.5 h-3.5 shrink-0 ml-2 transition-transform text-[#000000] ${
                      isSelected ? 'translate-x-0.5' : 'opacity-40'
                    }`}
                  />
                </div>
              )
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="flex items-center justify-between px-4 py-2 bg-[#faedcd]/40 border-t border-[#ccd5ae] text-xs text-[#333333]">
          <div className="flex items-center gap-3 text-[11px]">
            <span><kbd className="px-1 py-0.5 rounded bg-white border border-[#ccd5ae] font-mono text-[9px] text-[#000000]">↑↓</kbd> navigate</span>
            <span><kbd className="px-1 py-0.5 rounded bg-white border border-[#ccd5ae] font-mono text-[9px] text-[#000000]">↵</kbd> select</span>
            <span><kbd className="px-1 py-0.5 rounded bg-white border border-[#ccd5ae] font-mono text-[9px] text-[#000000]">ESC</kbd> close</span>
          </div>
          <span className="text-[11px] font-semibold text-[#000000]">Chatur Global Search</span>
        </div>
      </div>
    </div>
  )
}
