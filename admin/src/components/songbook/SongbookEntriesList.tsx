import { useState, useEffect } from "react";
import { SongbookEntry, api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SongbookEntryModal } from "./SongbookEntryModal";
import { Plus, Search, Eye, Edit2, Book, Calendar, User, Hash, Filter, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export function SongbookEntriesList() {
  const [entries, setEntries] = useState<SongbookEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSongbook, setSelectedSongbook] = useState<string>("all");
  const [selectedComposer, setSelectedComposer] = useState<string>("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<SongbookEntry | null>(null);
  const [songbookNames, setSongbookNames] = useState<string[]>([]);
  const { toast } = useToast();

  // Load initial data
  useEffect(() => {
    loadEntries();
    loadSongbookNames();
  }, []);

  const loadEntries = async () => {
    try {
      setLoading(true);
      const data = await api.songbook.getEntries({
        limit: 100, // TODO: implement pagination
      });
      setEntries(data);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load songbook entries",
        variant: "destructive",
      });
      console.error("Failed to load entries:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadSongbookNames = async () => {
    try {
      const names = await api.songbook.getSongbookNames();
      setSongbookNames(names);
    } catch (error) {
      console.error("Failed to load songbook names:", error);
    }
  };

  // Filter entries based on search and filters
  const filteredEntries = entries.filter(entry => {
    const matchesSearch = searchTerm === "" || 
      entry.printed_song_title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.eng_title_transl?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.modern_song_title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.composer?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.songbook_name.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesSongbook = selectedSongbook === "all" || entry.songbook_name === selectedSongbook;
    
    const matchesComposer = selectedComposer === "all" || entry.composer === selectedComposer;

    return matchesSearch && matchesSongbook && matchesComposer;
  });

  const openAddModal = () => {
    setEditingEntry(null);
    setIsModalOpen(true);
  };

  const openEditModal = (entry: SongbookEntry) => {
    setEditingEntry(entry);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingEntry(null);
  };

  const handleSaveEntry = async (entryData: Omit<SongbookEntry, 'id' | 'created_at' | 'updated_at'>) => {
    try {
      if (editingEntry) {
        // Update existing entry
        const updated = await api.songbook.updateEntry(editingEntry.id!, entryData);
        setEntries(entries.map(e => e.id === editingEntry.id ? updated : e));
        toast({
          title: "Success",
          description: "Songbook entry updated successfully",
        });
      } else {
        // Create new entry
        const created = await api.songbook.createEntry(entryData);
        setEntries([...entries, created]);
        toast({
          title: "Success", 
          description: "Songbook entry created successfully",
        });
      }
      closeModal();
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to ${editingEntry ? 'update' : 'create'} entry`,
        variant: "destructive",
      });
      console.error("Failed to save entry:", error);
    }
  };

  const handleDeleteEntry = async (entry: SongbookEntry) => {
    if (!window.confirm(`Are you sure you want to delete the entry for "${entry.printed_song_title}"?`)) {
      return;
    }

    try {
      await api.songbook.deleteEntry(entry.id!);
      setEntries(entries.filter(e => e.id !== entry.id));
      toast({
        title: "Success",
        description: "Songbook entry deleted successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete entry",
        variant: "destructive",
      });
      console.error("Failed to delete entry:", error);
    }
  };

  // Get unique composers for filter
  const uniqueComposers = Array.from(new Set(entries.map(e => e.composer).filter(Boolean))).sort();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading songbook entries...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Songbook Entries</h1>
          <p className="text-muted-foreground">
            Manage songs as they appear in published songbooks
          </p>
        </div>
        <Button onClick={openAddModal} className="bg-ocean-deep hover:bg-ocean-deep/90">
          <Plus className="w-4 h-4 mr-2" />
          Add Entry
        </Button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex items-center space-x-2 flex-1">
          <Search className="w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by title, composer, or songbook..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
        </div>
        
        <div className="flex gap-2">
          <Select value={selectedSongbook} onValueChange={setSelectedSongbook}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Filter by songbook" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Songbooks</SelectItem>
              {songbookNames.map(name => (
                <SelectItem key={name} value={name}>{name}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={selectedComposer} onValueChange={setSelectedComposer}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Filter by composer" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Composers</SelectItem>
              {uniqueComposers.map(composer => (
                <SelectItem key={composer} value={composer!}>{composer}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Book className="w-4 h-4 text-ocean-deep" />
              <div>
                <div className="text-2xl font-bold">{filteredEntries.length}</div>
                <div className="text-xs text-muted-foreground">Entries</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Book className="w-4 h-4 text-coral" />
              <div>
                <div className="text-2xl font-bold">
                  {new Set(filteredEntries.map(e => e.songbook_name)).size}
                </div>
                <div className="text-xs text-muted-foreground">Songbooks</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-tropical" />
              <div>
                <div className="text-2xl font-bold">
                  {new Set(filteredEntries.map(e => e.composer).filter(Boolean)).size}
                </div>
                <div className="text-xs text-muted-foreground">Composers</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Hash className="w-4 h-4 text-sunset" />
              <div>
                <div className="text-2xl font-bold">
                  {filteredEntries.filter(e => e.page).length}
                </div>
                <div className="text-xs text-muted-foreground">With Pages</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Entries Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredEntries.map((entry) => (
          <Card key={entry.id} className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="space-y-1 flex-1">
                  <CardTitle className="text-lg leading-tight">
                    {entry.printed_song_title}
                  </CardTitle>
                  {entry.eng_title_transl && (
                    <p className="text-sm text-muted-foreground">
                      {entry.eng_title_transl}
                    </p>
                  )}
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => openEditModal(entry)}
                  >
                    <Edit2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                <Book className="w-4 h-4 text-muted-foreground" />
                <span className="text-foreground font-medium">
                  {entry.songbook_name}
                </span>
              </div>

              {entry.composer && (
                <div className="flex items-center gap-2 text-sm">
                  <User className="w-4 h-4 text-muted-foreground" />
                  <span className="text-foreground">
                    {entry.composer}
                  </span>
                </div>
              )}

              <div className="flex flex-wrap gap-1">
                {entry.page && (
                  <Badge variant="outline" className="text-xs">
                    Page {entry.page}
                  </Badge>
                )}
                {entry.pub_year && (
                  <Badge variant="secondary" className="text-xs">
                    <Calendar className="w-3 h-3 mr-1" />
                    {entry.pub_year}
                  </Badge>
                )}
                {entry.diacritics && (
                  <Badge 
                    variant="outline" 
                    className={`text-xs ${
                      entry.diacritics === 'Yes' ? 'bg-green-50 text-green-700 border-green-200' :
                      entry.diacritics === 'No' ? 'bg-red-50 text-red-700 border-red-200' :
                      'bg-yellow-50 text-yellow-700 border-yellow-200'
                    }`}
                  >
                    {entry.diacritics} diacritics
                  </Badge>
                )}
              </div>

              {entry.additional_information && (
                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {entry.additional_information}
                  </p>
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => openEditModal(entry)}
                  className="flex-1"
                >
                  <Edit2 className="w-3 h-3 mr-1" />
                  Edit
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDeleteEntry(entry)}
                  className="text-red-600 hover:text-red-700"
                >
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredEntries.length === 0 && !loading && (
        <div className="text-center py-8">
          <Book className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No entries found</h3>
          <p className="text-muted-foreground">
            {searchTerm || selectedSongbook !== "all" || selectedComposer !== "all" 
              ? "Try adjusting your search or filters" 
              : "Start by adding your first songbook entry"
            }
          </p>
        </div>
      )}

      <SongbookEntryModal
        isOpen={isModalOpen}
        onClose={closeModal}
        onSave={handleSaveEntry}
        entry={editingEntry}
      />
    </div>
  );
}