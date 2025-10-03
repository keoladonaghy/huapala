import { useState, useEffect } from "react";
import { CanonicalMele, MeleFormData } from "@/types/mele";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Music, FileText, Settings, BarChart3 } from "lucide-react";

interface MeleFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (mele: Omit<CanonicalMele, "canonical_mele_id">) => void;
  mele?: CanonicalMele | null;
}

export function MeleFormModal({ isOpen, onClose, onSubmit, mele }: MeleFormModalProps) {
  const [formData, setFormData] = useState<MeleFormData>({
    canonical_title_hawaiian: "",
    canonical_title_english: "",
    primary_composer: "",
    translator: "",
    source_file: "",
    original_file: "",
    exported_at: "",
    source: "",
    processed_at: "",
    parsing_quality_score: "",
    total_sections: "",
    total_lines: "",
    verses_summary: "",
  });

  useEffect(() => {
    if (mele) {
      setFormData({
        canonical_title_hawaiian: mele.canonical_title_hawaiian,
        canonical_title_english: mele.canonical_title_english || "",
        primary_composer: mele.primary_composer,
        translator: mele.translator || "",
        source_file: mele.source_file,
        original_file: mele.processing_metadata.original_file || "",
        exported_at: mele.processing_metadata.exported_at || "",
        source: mele.processing_metadata.source || "",
        processed_at: mele.processing_metadata.processed_at || "",
        parsing_quality_score: mele.processing_metadata.parsing_quality_score?.toString() || "",
        total_sections: mele.processing_metadata.total_sections.toString(),
        total_lines: mele.processing_metadata.total_lines.toString(),
        verses_summary: `${mele.verses.length} section(s): ${mele.verses.map(v => v.label || `${v.type} ${v.number || ""}`).join(", ")}`,
      });
    } else {
      setFormData({
        canonical_title_hawaiian: "",
        canonical_title_english: "",
        primary_composer: "",
        translator: "",
        source_file: "",
        original_file: "",
        exported_at: "",
        source: "",
        processed_at: "",
        parsing_quality_score: "",
        total_sections: "",
        total_lines: "",
        verses_summary: "",
      });
    }
  }, [mele, isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.canonical_title_hawaiian.trim()) return;

    const processedMele = {
      canonical_title_hawaiian: formData.canonical_title_hawaiian.trim(),
      canonical_title_english: formData.canonical_title_english.trim(),
      primary_composer: formData.primary_composer.trim(),
      translator: formData.translator.trim(),
      source_file: formData.source_file.trim(),
      processing_metadata: {
        original_file: formData.original_file.trim() || undefined,
        exported_at: formData.exported_at.trim() || undefined,
        source: formData.source.trim() || undefined,
        processed_at: formData.processed_at.trim() || undefined,
        parsing_quality_score: formData.parsing_quality_score ? parseInt(formData.parsing_quality_score) : undefined,
        total_sections: formData.total_sections ? parseInt(formData.total_sections) : 0,
        total_lines: formData.total_lines ? parseInt(formData.total_lines) : 0,
      },
      verses: mele?.verses || [], // Keep existing verses structure
    };

    onSubmit(processedMele);
    onClose();
  };

  const formatComposer = (composer: string) => {
    // Clean up HTML entities
    return composer.replace(/&#8216;/g, "'").replace(/&auml;/g, "ä");
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>
            {mele ? "Edit Mele" : "Add New Mele"}
          </DialogTitle>
          <DialogDescription>
            {mele ? "Update mele metadata information" : "Add a new mele to the database"}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex-1 overflow-hidden flex flex-col">
          <Tabs defaultValue="basic" className="flex-1 overflow-hidden flex flex-col">
            <TabsList className="grid w-full grid-cols-4 flex-shrink-0">
              <TabsTrigger value="basic" className="flex items-center gap-2">
                <Music className="w-4 h-4" />
                Basic Info
              </TabsTrigger>
              <TabsTrigger value="people" className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                People & Sources
              </TabsTrigger>
              <TabsTrigger value="processing" className="flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Processing Data
              </TabsTrigger>
              <TabsTrigger value="content" className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Content Summary
              </TabsTrigger>
            </TabsList>
            
            <div className="flex-1 overflow-y-auto">
              <TabsContent value="basic" className="space-y-4 p-4">
                <div className="space-y-2">
                  <Label htmlFor="canonical_title_hawaiian">Hawaiian Title *</Label>
                  <Input
                    id="canonical_title_hawaiian"
                    value={formData.canonical_title_hawaiian}
                    onChange={(e) => setFormData(prev => ({ ...prev, canonical_title_hawaiian: e.target.value }))}
                    placeholder="Enter Hawaiian title"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="canonical_title_english">English Title</Label>
                  <Input
                    id="canonical_title_english"
                    value={formData.canonical_title_english}
                    onChange={(e) => setFormData(prev => ({ ...prev, canonical_title_english: e.target.value }))}
                    placeholder="Enter English title (if available)"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="canonical_mele_id">Canonical Mele ID</Label>
                  <Input
                    id="canonical_mele_id"
                    value={mele?.canonical_mele_id || ""}
                    placeholder="Auto-generated from Hawaiian title"
                    disabled
                    className="bg-muted"
                  />
                  <p className="text-xs text-muted-foreground">
                    This ID is automatically generated and cannot be edited
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="people" className="space-y-4 p-4">
                <div className="space-y-2">
                  <Label htmlFor="primary_composer">Primary Composer</Label>
                  <Input
                    id="primary_composer"
                    value={formatComposer(formData.primary_composer)}
                    onChange={(e) => setFormData(prev => ({ ...prev, primary_composer: e.target.value }))}
                    placeholder="Enter composer name(s)"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="translator">Translator</Label>
                  <Input
                    id="translator"
                    value={formData.translator}
                    onChange={(e) => setFormData(prev => ({ ...prev, translator: e.target.value }))}
                    placeholder="Enter translator name (if applicable)"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="source_file">Source File</Label>
                  <Input
                    id="source_file"
                    value={formData.source_file}
                    onChange={(e) => setFormData(prev => ({ ...prev, source_file: e.target.value }))}
                    placeholder="Original source file path/name"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="original_file">Original File</Label>
                  <Input
                    id="original_file"
                    value={formData.original_file}
                    onChange={(e) => setFormData(prev => ({ ...prev, original_file: e.target.value }))}
                    placeholder="Original file location in processing metadata"
                  />
                </div>
              </TabsContent>

              <TabsContent value="processing" className="space-y-4 p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="exported_at">Exported At</Label>
                    <Input
                      id="exported_at"
                      value={formData.exported_at}
                      onChange={(e) => setFormData(prev => ({ ...prev, exported_at: e.target.value }))}
                      placeholder="e.g., 2025-09-19T16:56:40.902731"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="processed_at">Processed At</Label>
                    <Input
                      id="processed_at"
                      value={formData.processed_at}
                      onChange={(e) => setFormData(prev => ({ ...prev, processed_at: e.target.value }))}
                      placeholder="e.g., 2025-09-19T17:57:49.758898"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="source">Source Type</Label>
                    <Input
                      id="source"
                      value={formData.source}
                      onChange={(e) => setFormData(prev => ({ ...prev, source: e.target.value }))}
                      placeholder="e.g., database_export, file_import"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="parsing_quality_score">Parsing Quality Score</Label>
                    <Input
                      id="parsing_quality_score"
                      type="number"
                      value={formData.parsing_quality_score}
                      onChange={(e) => setFormData(prev => ({ ...prev, parsing_quality_score: e.target.value }))}
                      placeholder="Quality score (0-100)"
                      min="0"
                      max="100"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="total_sections">Total Sections</Label>
                    <Input
                      id="total_sections"
                      type="number"
                      value={formData.total_sections}
                      onChange={(e) => setFormData(prev => ({ ...prev, total_sections: e.target.value }))}
                      placeholder="Number of sections"
                      min="0"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="total_lines">Total Lines</Label>
                    <Input
                      id="total_lines"
                      type="number"
                      value={formData.total_lines}
                      onChange={(e) => setFormData(prev => ({ ...prev, total_lines: e.target.value }))}
                      placeholder="Number of lines"
                      min="0"
                    />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="content" className="space-y-4 p-4">
                <div className="space-y-2">
                  <Label htmlFor="verses_summary">Verses & Structure Summary</Label>
                  <Textarea
                    id="verses_summary"
                    value={formData.verses_summary}
                    onChange={(e) => setFormData(prev => ({ ...prev, verses_summary: e.target.value }))}
                    placeholder="Brief summary of verse structure (full verse data is preserved separately)"
                    rows={3}
                    className="bg-muted"
                  />
                  <p className="text-xs text-muted-foreground">
                    This field shows a summary only. The complete verse-by-verse Hawaiian and English text data is preserved separately and not editable through this form to save space.
                  </p>
                </div>

                <div className="p-4 border rounded-lg bg-muted/50">
                  <h4 className="font-medium mb-2">Content Data Preserved</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• Complete verse-by-verse structure</li>
                    <li>• Line-by-line Hawaiian and English text</li>
                    <li>• Verse types (verse, chorus/hui)</li>
                    <li>• Line numbering and ordering</li>
                    <li>• Bilingual text alignment</li>
                  </ul>
                </div>
              </TabsContent>
            </div>
          </Tabs>

          <DialogFooter className="flex-shrink-0 pt-4 border-t">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" className="bg-ocean-deep hover:bg-ocean-deep/90">
              {mele ? "Update Mele" : "Add Mele"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}