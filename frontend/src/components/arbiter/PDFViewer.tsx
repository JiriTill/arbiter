"use client";

import { useState, useEffect, useRef } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Loader2, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure worker
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PDFViewerProps {
    url: string;
    initialPage?: number;
    quote?: string;
    gameName?: string;
    sourceName?: string;
}

export function PDFViewer({ url, initialPage = 1, quote, gameName, sourceName }: PDFViewerProps) {
    const [numPages, setNumPages] = useState<number>(0);
    const [pageNumber, setPageNumber] = useState(initialPage);
    const [scale, setScale] = useState(1.0);
    const [width, setWidth] = useState(600);
    const containerRef = useRef<HTMLDivElement>(null);

    // Responsive width
    useEffect(() => {
        const updateWidth = () => {
            if (containerRef.current) {
                setWidth(containerRef.current.clientWidth - 32); // margin
            } else {
                setWidth(Math.min(window.innerWidth - 32, 800));
            }
        };

        updateWidth();
        window.addEventListener("resize", updateWidth);
        return () => window.removeEventListener("resize", updateWidth);
    }, []);

    // Initial page sync
    useEffect(() => {
        if (initialPage) setPageNumber(initialPage);
    }, [initialPage]);

    function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
        setNumPages(numPages);
    }

    function changePage(offset: number) {
        setPageNumber(prev => Math.min(Math.max(1, prev + offset), numPages));
    }

    function jumpToPage(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        const input = e.currentTarget.elements.namedItem('page') as HTMLInputElement;
        if (input) {
            const val = parseInt(input.value);
            if (val >= 1 && val <= numPages) setPageNumber(val);
        }
    }

    return (
        <div className="flex flex-col w-full min-h-screen bg-gray-50 dark:bg-gray-950" ref={containerRef}>
            {/* Header / Banner */}
            {quote && (
                <div className="bg-amber-50 border-b border-amber-200 p-4 shadow-sm sticky top-0 z-20">
                    <div className="max-w-4xl mx-auto">
                        <p className="text-xs font-semibold text-amber-800 uppercase tracking-wide mb-1">
                            Look for this quote on page {initialPage}
                        </p>
                        <p className="text-sm text-gray-800 italic border-l-4 border-amber-400 pl-3 py-1 bg-white/50 rounded">
                            &quot;{quote}&quot;
                        </p>
                    </div>
                </div>
            )}

            {/* Toolbar */}
            <div className="bg-white dark:bg-gray-900 border-b p-2 flex items-center justify-between sticky top-[quote ? 'auto' : 0] z-10 shadow-sm">
                <div className="flex items-center gap-2">
                    <div className="hidden sm:block">
                        <h1 className="text-sm font-semibold truncate max-w-[200px]">{gameName}</h1>
                        <p className="text-xs text-muted-foreground truncate max-w-[200px]">{sourceName}</p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <Button variant="ghost" size="icon" onClick={() => changePage(-1)} disabled={pageNumber <= 1}>
                        <ChevronLeft className="h-4 w-4" />
                    </Button>

                    <form onSubmit={jumpToPage} className="flex items-center gap-1">
                        <input
                            name="page"
                            type="number"
                            min={1}
                            max={numPages || undefined}
                            defaultValue={pageNumber}
                            key={pageNumber}
                            className="w-12 h-8 text-sm text-center border rounded bg-transparent"
                        />
                        <span className="text-sm font-medium text-muted-foreground">
                            / {numPages || "--"}
                        </span>
                    </form>

                    <Button variant="ghost" size="icon" onClick={() => changePage(1)} disabled={pageNumber >= numPages}>
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>

                <div className="flex items-center gap-1">
                    <Button variant="ghost" size="icon" onClick={() => setScale(s => Math.max(0.5, s - 0.1))}>
                        <ZoomOut className="h-4 w-4" />
                    </Button>
                    <span className="text-xs w-8 text-center">{Math.round(scale * 100)}%</span>
                    <Button variant="ghost" size="icon" onClick={() => setScale(s => Math.min(2.5, s + 0.1))}>
                        <ZoomIn className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* PDF Content */}
            <div className="flex-1 overflow-auto flex justify-center p-4">
                <Document
                    file={url}
                    onLoadSuccess={onDocumentLoadSuccess}
                    loading={
                        <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
                            <Loader2 className="h-8 w-8 animate-spin mb-4" />
                            <p>Loading PDF...</p>
                        </div>
                    }
                    error={
                        <div className="flex flex-col items-center justify-center p-12 text-red-500">
                            <p>Failed to load PDF.</p>
                            <Button
                                variant="outline"
                                className="mt-4"
                                onClick={() => window.open(url, '_blank')}
                            >
                                <ExternalLink className="mr-2 h-4 w-4" />
                                Open Externally
                            </Button>
                        </div>
                    }
                >
                    <Page
                        pageNumber={pageNumber}
                        scale={scale}
                        width={width}
                        renderTextLayer={true}
                        renderAnnotationLayer={true}
                        className="shadow-lg"
                    />
                </Document>
            </div>
        </div>
    );
}
