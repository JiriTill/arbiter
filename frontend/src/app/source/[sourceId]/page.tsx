import dynamic from "next/dynamic";
import { Loader2 } from "lucide-react";

// Dynamically import PDFViewer with SSR disabled to prevent window/canvas issues
const PDFViewer = dynamic(
    () => import("@/components/arbiter/PDFViewer").then(mod => mod.PDFViewer),
    {
        ssr: false,
        loading: () => (
            <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-950">
                <div className="flex flex-col items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-8 w-8 animate-spin" />
                    <p>Loading Viewer...</p>
                </div>
            </div>
        )
    }
);

export default function SourceViewerPage({
    params,
    searchParams
}: {
    params: { sourceId: string },
    searchParams: { page?: string, quote?: string }
}) {
    const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/sources/${params.sourceId}/pdf`;

    // Parse page with fallback
    let page = 1;
    if (searchParams.page) {
        const val = parseInt(searchParams.page);
        if (!isNaN(val)) page = val;
    }

    return (
        <PDFViewer
            url={url}
            initialPage={page}
            quote={searchParams.quote}
        />
    );
}
