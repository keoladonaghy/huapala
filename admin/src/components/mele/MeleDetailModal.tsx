import { CanonicalMele } from "@/types/mele";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Music, Languages, User, FileText } from "lucide-react";

interface MeleDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  mele: CanonicalMele | null;
}

export function MeleDetailModal({ isOpen, onClose, mele }: MeleDetailModalProps) {
  if (!mele) return null;

  const formatComposer = (composer: string) => {
    if (!composer || composer.includes("<!--") || composer.includes("Page")) {
      return "Unknown";
    }
    return composer.replace(/&#8216;/g, "'").replace(/&auml;/g, "ä");
  };

  const renderVerse = (verse: any, index: number) => {
    return (
      <div key={verse.id || index} className="space-y-3">
        <div className="flex items-center gap-2">
          <Badge variant={verse.type === "chorus" ? "default" : "secondary"}>
            {verse.label || `${verse.type === "chorus" ? "Hui" : "Verse"} ${verse.number || index + 1}`}
          </Badge>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Hawaiian text */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-coral">Hawaiian</h4>
            <div className="space-y-1">
              {verse.lines ? (
                verse.lines.map((line: any, lineIndex: number) => (
                  <p key={line.id || lineIndex} className="text-sm leading-relaxed">
                    {line.hawaiian_text}
                  </p>
                ))
              ) : verse.hawaiian_lines ? (
                verse.hawaiian_lines.map((line: string, lineIndex: number) => (
                  <p key={lineIndex} className="text-sm leading-relaxed">
                    {line}
                  </p>
                ))
              ) : verse.hawaiian_text ? (
                <p className="text-sm leading-relaxed whitespace-pre-line">
                  {verse.hawaiian_text}
                </p>
              ) : null}
            </div>
          </div>

          {/* English text */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-tropical">English</h4>
            <div className="space-y-1">
              {verse.lines ? (
                verse.lines.map((line: any, lineIndex: number) => (
                  <p key={line.id || lineIndex} className="text-sm leading-relaxed text-muted-foreground">
                    {line.english_text}
                  </p>
                ))
              ) : verse.english_lines ? (
                verse.english_lines.map((line: string, lineIndex: number) => (
                  <p key={lineIndex} className="text-sm leading-relaxed text-muted-foreground">
                    {line}
                  </p>
                ))
              ) : verse.english_text ? (
                <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-line">
                  {verse.english_text}
                </p>
              ) : (
                <p className="text-sm text-muted-foreground italic">No translation available</p>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="text-xl">{mele.canonical_title_hawaiian}</DialogTitle>
          {mele.canonical_title_english && (
            <DialogDescription className="text-base">
              {mele.canonical_title_english}
            </DialogDescription>
          )}
        </DialogHeader>

        <div className="flex-shrink-0 space-y-4 pb-4">
          {/* Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium">Composer:</span>
              <span>{formatComposer(mele.primary_composer)}</span>
            </div>
            
            {mele.translator && (
              <div className="flex items-center gap-2">
                <Languages className="w-4 h-4 text-muted-foreground" />
                <span className="font-medium">Translator:</span>
                <span>{mele.translator}</span>
              </div>
            )}

            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium">Source:</span>
              <span className="text-muted-foreground">{mele.source_file}</span>
            </div>

            <div className="flex items-center gap-2">
              <Music className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium">Structure:</span>
              <div className="flex gap-1">
                <Badge variant="outline" className="text-xs">
                  {mele.verses.filter(v => v.type === "verse").length} verses
                </Badge>
                {mele.verses.filter(v => v.type === "chorus").length > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    {mele.verses.filter(v => v.type === "chorus").length} choruses
                  </Badge>
                )}
              </div>
            </div>
          </div>

          <Separator />
        </div>

        {/* Scrollable content */}
        <ScrollArea className="flex-1">
          <div className="space-y-6 pr-4">
            {mele.verses
              .sort((a, b) => a.order - b.order)
              .map((verse, index) => renderVerse(verse, index))}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}