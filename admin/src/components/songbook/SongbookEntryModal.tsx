import { useState, useEffect } from "react";
import { SongbookEntry, api } from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Book, Save, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface SongbookEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (entry: Omit<SongbookEntry, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  entry?: SongbookEntry | null;
}

export function SongbookEntryModal({ isOpen, onClose, onSave, entry }: SongbookEntryModalProps) {
  const [formData, setFormData] = useState<Omit<SongbookEntry, 'id' | 'created_at' | 'updated_at'>>({
    printed_song_title: '',
    eng_title_transl: '',
    modern_song_title: '',
    scripped_song_title: '',
    song_title: '',
    songbook_name: '',
    page: undefined,
    pub_year: undefined,
    diacritics: undefined,
    composer: '',
    additional_information: '',
    email_address: '',
  });
  
  const [songbookNames, setSongbookNames] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const { toast } = useToast();

  // Load songbook names for dropdown
  useEffect(() => {
    if (isOpen) {
      loadSongbookNames();
    }
  }, [isOpen]);

  // Populate form when editing
  useEffect(() => {
    if (entry) {
      setFormData({
        printed_song_title: entry.printed_song_title || '',
        eng_title_transl: entry.eng_title_transl || '',
        modern_song_title: entry.modern_song_title || '',
        scripped_song_title: entry.scripped_song_title || '',
        song_title: entry.song_title || '',
        songbook_name: entry.songbook_name || '',
        page: entry.page,
        pub_year: entry.pub_year,
        diacritics: entry.diacritics,
        composer: entry.composer || '',
        additional_information: entry.additional_information || '',
        email_address: entry.email_address || '',
      });
    } else {
      // Reset form for new entry
      setFormData({
        printed_song_title: '',
        eng_title_transl: '',
        modern_song_title: '',
        scripped_song_title: '',
        song_title: '',
        songbook_name: '',
        page: undefined,
        pub_year: undefined,
        diacritics: undefined,
        composer: '',
        additional_information: '',
        email_address: '',
      });
    }
    setErrors({});
  }, [entry, isOpen]);

  const loadSongbookNames = async () => {
    try {
      const names = await api.songbook.getSongbookNames();
      setSongbookNames(names);
    } catch (error) {
      console.error("Failed to load songbook names:", error);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Required fields
    if (!formData.printed_song_title.trim()) {
      newErrors.printed_song_title = "Song title is required";
    }
    if (!formData.songbook_name.trim()) {
      newErrors.songbook_name = "Songbook name is required";
    }

    // Validate year range
    if (formData.pub_year && (formData.pub_year < 1800 || formData.pub_year > 2100)) {
      newErrors.pub_year = "Publication year must be between 1800 and 2100";
    }

    // Validate page number
    if (formData.page && formData.page < 1) {
      newErrors.page = "Page number must be positive";
    }

    // Validate email format
    if (formData.email_address && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email_address)) {
      newErrors.email_address = "Invalid email format";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      // Clean up the data - remove empty strings and convert to appropriate types
      const cleanedData = {
        ...formData,
        eng_title_transl: formData.eng_title_transl || undefined,
        modern_song_title: formData.modern_song_title || undefined,
        scripped_song_title: formData.scripped_song_title || undefined,
        song_title: formData.song_title || undefined,
        composer: formData.composer || undefined,
        additional_information: formData.additional_information || undefined,
        email_address: formData.email_address || undefined,
        page: formData.page || undefined,
        pub_year: formData.pub_year || undefined,
      };

      await onSave(cleanedData);
      onClose();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save entry. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof typeof formData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Book className="h-5 w-5 text-ocean-deep" />
            {entry ? 'Edit Songbook Entry' : 'Add New Songbook Entry'}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Primary Song Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Song Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="printed_song_title">
                  Printed Song Title *
                </Label>
                <Input
                  id="printed_song_title"
                  value={formData.printed_song_title}
                  onChange={(e) => handleInputChange('printed_song_title', e.target.value)}
                  placeholder="Title as it appears in the songbook"
                  className={errors.printed_song_title ? 'border-red-500' : ''}
                />
                {errors.printed_song_title && (
                  <p className="text-sm text-red-500">{errors.printed_song_title}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="eng_title_transl">English Translation</Label>
                <Input
                  id="eng_title_transl"
                  value={formData.eng_title_transl}
                  onChange={(e) => handleInputChange('eng_title_transl', e.target.value)}
                  placeholder="English translation of title"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="modern_song_title">Modern Song Title</Label>
                <Input
                  id="modern_song_title"
                  value={formData.modern_song_title}
                  onChange={(e) => handleInputChange('modern_song_title', e.target.value)}
                  placeholder="Modern/standardized title"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="scripped_song_title">Scripted Song Title</Label>
                <Input
                  id="scripped_song_title"
                  value={formData.scripped_song_title}
                  onChange={(e) => handleInputChange('scripped_song_title', e.target.value)}
                  placeholder="Alternative scripted title"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="song_title">Additional Title</Label>
              <Input
                id="song_title"
                value={formData.song_title}
                onChange={(e) => handleInputChange('song_title', e.target.value)}
                placeholder="Additional title field"
              />
            </div>
          </div>

          {/* Songbook Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Songbook Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="songbook_name">Songbook Name *</Label>
                <Select
                  value={formData.songbook_name}
                  onValueChange={(value) => handleInputChange('songbook_name', value)}
                >
                  <SelectTrigger className={errors.songbook_name ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select or type songbook name" />
                  </SelectTrigger>
                  <SelectContent>
                    {songbookNames.map(name => (
                      <SelectItem key={name} value={name}>{name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  value={formData.songbook_name}
                  onChange={(e) => handleInputChange('songbook_name', e.target.value)}
                  placeholder="Or type new songbook name"
                  className="mt-2"
                />
                {errors.songbook_name && (
                  <p className="text-sm text-red-500">{errors.songbook_name}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="page">Page Number</Label>
                <Input
                  id="page"
                  type="number"
                  min="1"
                  value={formData.page || ''}
                  onChange={(e) => handleInputChange('page', e.target.value ? parseInt(e.target.value) : undefined)}
                  placeholder="Page number"
                  className={errors.page ? 'border-red-500' : ''}
                />
                {errors.page && (
                  <p className="text-sm text-red-500">{errors.page}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="pub_year">Publication Year</Label>
                <Input
                  id="pub_year"
                  type="number"
                  min="1800"
                  max="2100"
                  value={formData.pub_year || ''}
                  onChange={(e) => handleInputChange('pub_year', e.target.value ? parseInt(e.target.value) : undefined)}
                  placeholder="e.g., 1985"
                  className={errors.pub_year ? 'border-red-500' : ''}
                />
                {errors.pub_year && (
                  <p className="text-sm text-red-500">{errors.pub_year}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="diacritics">Diacritics Usage</Label>
                <Select
                  value={formData.diacritics || ''}
                  onValueChange={(value) => handleInputChange('diacritics', value as any)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select diacritics usage" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Yes">Yes</SelectItem>
                    <SelectItem value="No">No</SelectItem>
                    <SelectItem value="Inconsistent">Inconsistent</SelectItem>
                    <SelectItem value="Unknown">Unknown</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="composer">Composer</Label>
                <Input
                  id="composer"
                  value={formData.composer}
                  onChange={(e) => handleInputChange('composer', e.target.value)}
                  placeholder="Song composer/author"
                />
              </div>
            </div>
          </div>

          {/* Additional Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Additional Information</h3>
            
            <div className="space-y-2">
              <Label htmlFor="additional_information">Notes</Label>
              <Textarea
                id="additional_information"
                value={formData.additional_information}
                onChange={(e) => handleInputChange('additional_information', e.target.value)}
                placeholder="Additional notes about the song or entry"
                className="min-h-[80px]"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email_address">Contributor Email</Label>
              <Input
                id="email_address"
                type="email"
                value={formData.email_address}
                onChange={(e) => handleInputChange('email_address', e.target.value)}
                placeholder="Contact email for contributor"
                className={errors.email_address ? 'border-red-500' : ''}
              />
              {errors.email_address && (
                <p className="text-sm text-red-500">{errors.email_address}</p>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 pt-4">
            <Button
              type="submit"
              disabled={loading}
              className="bg-gradient-to-r from-ocean-deep to-ocean-light hover:from-ocean-light hover:to-tropical"
            >
              <Save className="h-4 w-4 mr-2" />
              {loading ? 'Saving...' : 'Save Entry'}
            </Button>
            <Button type="button" variant="outline" onClick={onClose}>
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}