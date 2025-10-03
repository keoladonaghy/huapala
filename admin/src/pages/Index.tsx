import { useState } from "react";
import { Navigation } from "@/components/ui/navigation";
import { Dashboard } from "@/components/dashboard/Dashboard";
import { SongsList } from "@/components/songs/SongsList";
import { AddEntryForm } from "@/components/forms/AddEntryForm";
import { PeopleList } from "@/components/people/PeopleList";
import { MeleList } from "@/components/mele/MeleList";
import { SongbookEntriesList } from "@/components/songbook/SongbookEntriesList";
import { SuggestedLinkages } from "@/components/linkages/SuggestedLinkages";

const Index = () => {
  const [currentPage, setCurrentPage] = useState("dashboard");

  const renderPage = () => {
    switch (currentPage) {
      case "dashboard":
        return <Dashboard onPageChange={setCurrentPage} />;
      case "songbook-entries":
        return <SongbookEntriesList />;
      case "linkages":
        return <SuggestedLinkages />;
      case "songs":
        return <MeleList />;
      case "artists":
        return <PeopleList />;
      case "search":
        return <div className="p-6"><h1 className="text-3xl font-bold">Search - Coming Soon</h1></div>;
      case "add":
        return <AddEntryForm />;
      case "settings":
        return <div className="p-6"><h1 className="text-3xl font-bold">Settings - Coming Soon</h1></div>;
      default:
        return <Dashboard onPageChange={setCurrentPage} />;
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Navigation currentPage={currentPage} onPageChange={setCurrentPage} />
      <main className="flex-1 overflow-auto">
        {renderPage()}
      </main>
    </div>
  );
};

export default Index;
