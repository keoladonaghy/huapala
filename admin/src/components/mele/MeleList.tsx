import { useState } from "react";
import { CanonicalMele } from "@/types/mele";
import { realMeleData } from "@/data/mockMele";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { MeleDetailModal } from "./MeleDetailModal";
import { MeleFormModal } from "./MeleFormModal";
import { Plus, Search, Eye, Edit2, Music, Languages, User, Calendar, FileText } from "lucide-react";

export function MeleList() {
  const [mele, setMele] = useState<CanonicalMele[]>(realMeleData);
  const [searchTerm, setSearchTerm] = useState("");
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [selectedMele, setSelectedMele] = useState<CanonicalMele | null>(null);
  const [editingMele, setEditingMele] = useState<CanonicalMele | null>(null);

  const filteredMele = mele.filter(song =>
    song.canonical_title_hawaiian.toLowerCase().includes(searchTerm.toLowerCase()) ||
    song.canonical_title_english.toLowerCase().includes(searchTerm.toLowerCase()) ||
    song.primary_composer.toLowerCase().includes(searchTerm.toLowerCase()) ||
    song.translator.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const openDetailModal = (song: CanonicalMele) => {
    setSelectedMele(song);
    setIsDetailModalOpen(true);
  };

  const closeDetailModal = () => {
    setIsDetailModalOpen(false);
    setSelectedMele(null);
  };

  const openEditModal = (song: CanonicalMele) => {
    setEditingMele(song);
    setIsFormModalOpen(true);
  };

  const openAddModal = () => {
    setEditingMele(null);
    setIsFormModalOpen(true);
  };

  const closeFormModal = () => {
    setIsFormModalOpen(false);
    setEditingMele(null);
  };

  const handleAddMele = (newMele: Omit<CanonicalMele, "canonical_mele_id">) => {
    const meleData: CanonicalMele = {
      ...newMele,
      canonical_mele_id: newMele.canonical_title_hawaiian.toLowerCase().replace(/[^a-z0-9]/g, '_') + '_canonical',
    };
    setMele([...mele, meleData]);
  };

  const handleEditMele = (updatedMele: Omit<CanonicalMele, "canonical_mele_id">) => {
    if (editingMele) {
      const meleData: CanonicalMele = {
        ...updatedMele,
        canonical_mele_id: editingMele.canonical_mele_id,
      };
      setMele(mele.map(m => m.canonical_mele_id === editingMele.canonical_mele_id ? meleData : m));
      setEditingMele(null);
    }
  };

  const formatComposer = (composer: string) => {
    if (!composer || composer.includes("<!--") || composer.includes("Page")) {
      return "Unknown";
    }
    // Clean up HTML entities
    return composer.replace(/&#8216;/g, "'").replace(/&auml;/g, "ä");
  };

  const getVerseCount = (song: CanonicalMele) => {
    const verses = song.verses.filter(v => v.type === "verse").length;
    const choruses = song.verses.filter(v => v.type === "chorus").length;
    return { verses, choruses };
  };

  const getTotalLines = (song: CanonicalMele) => {
    return song.verses.reduce((total, verse) => {
      if (verse.lines) {
        return total + verse.lines.length;
      }
      if (verse.hawaiian_lines) {
        return total + verse.hawaiian_lines.length;
      }
      return total + 1;
    }, 0);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Mele Collection</h1>
          <p className="text-muted-foreground">Canonical Hawaiian songs with bilingual lyrics</p>
        </div>
        <Button onClick={openAddModal} className="bg-ocean-deep hover:bg-ocean-deep/90">
          <Plus className="w-4 h-4 mr-2" />
          Add Mele
        </Button>
      </div>

      <div className="flex items-center space-x-2">
        <Search className="w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search by title, composer, or translator..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredMele.map((song) => {
          const { verses, choruses } = getVerseCount(song);
          const totalLines = getTotalLines(song);
          
          return (
            <Card key={song.canonical_mele_id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="space-y-1 flex-1">
                    <CardTitle className="text-lg leading-tight">
                      {song.canonical_title_hawaiian}
                    </CardTitle>
                    {song.canonical_title_english && (
                      <p className="text-sm text-muted-foreground">
                        {song.canonical_title_english}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openEditModal(song)}
                    >
                      <Edit2 className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openDetailModal(song)}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2 text-sm">
                  <User className="w-4 h-4 text-muted-foreground" />
                  <span className="text-foreground">
                    {formatComposer(song.primary_composer)}
                  </span>
                </div>

                <div className="flex flex-wrap gap-1 mb-3">
                  <Badge variant="outline" className="text-xs">
                    <Music className="w-3 h-3 mr-1" />
                    {verses} verse{verses !== 1 ? 's' : ''}
                  </Badge>
                  {choruses > 0 && (
                    <Badge variant="secondary" className="text-xs">
                      {choruses} chorus{choruses !== 1 ? 'es' : ''}
                    </Badge>
                  )}
                  <Badge variant="outline" className="text-xs bg-tropical-light/20 text-tropical border-tropical-light">
                    {totalLines} lines
                  </Badge>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-muted-foreground" />
                    <span className="text-foreground">
                      {formatComposer(song.primary_composer) || "Unknown"}
                    </span>
                  </div>

                  {song.translator && (
                    <div className="flex items-center gap-2">
                      <Languages className="w-4 h-4 text-muted-foreground" />
                      <span className="text-muted-foreground">
                        Translated by: {song.translator}
                      </span>
                    </div>
                  )}

                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-muted-foreground" />
                    <span className="text-muted-foreground text-xs">
                      {song.source_file}
                    </span>
                  </div>

                  {song.processing_metadata.processed_at && (
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-muted-foreground" />
                      <span className="text-muted-foreground text-xs">
                        Processed: {new Date(song.processing_metadata.processed_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>

                {/* Preview of first verse */}
                {song.verses[0] && (
                  <div className="pt-2 border-t">
                    <p className="text-xs text-muted-foreground mb-1">Preview:</p>
                    <div className="text-xs space-y-1">
                      {song.verses[0].lines ? (
                        <p className="text-foreground italic">
                          {song.verses[0].lines[0]?.hawaiian_text}
                        </p>
                      ) : song.verses[0].hawaiian_text ? (
                        <p className="text-foreground italic line-clamp-2">
                          {song.verses[0].hawaiian_text.split(' ').slice(0, 8).join(' ')}...
                        </p>
                      ) : null}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {filteredMele.length === 0 && (
        <div className="text-center py-8">
          <Music className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No mele found</h3>
          <p className="text-muted-foreground">
            {searchTerm ? "Try adjusting your search terms" : "Start by adding your first mele"}
          </p>
        </div>
      )}

      <MeleDetailModal
        isOpen={isDetailModalOpen}
        onClose={closeDetailModal}
        mele={selectedMele}
      />

      <MeleFormModal
        isOpen={isFormModalOpen}
        onClose={closeFormModal}
        onSubmit={editingMele ? handleEditMele : handleAddMele}
        mele={editingMele}
      />
    </div>
  );
}