import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

interface AnalyticsEvent {
    event: string;
    page: string;
    userId?: string;
    timestamp: Date;
    metadata?: Record<string, any>
}

class AnalyticsService {
    private events: AnalyticsEvent[] = [];

    track(event: string, metadata?: Record<string, any>) {
        const analyticsEvent: AnalyticsEvent = {
            event,
            page: window.location.pathname,
            timestamp: new Date(),
            metadata
        }

        this.events.push(analyticsEvent)

        // In production send, to your analytics service
        console.log("Analytics Event", analyticsEvent)

        // / Example: Send to external service
    // fetch('/api/analytics', {
    //   method: 'POST',
    //   body: JSON.stringify(analyticsEvent)
    // });

    }
     getEvnts() {
        return this.events
     }
}

export const analytics = new AnalyticsService()

export const useAnalytics = () => {
    const location = useLocation()

    useEffect(() => {
        analytics.track('page view', {
            path: location.pathname,
            seacrh: location.search
        });
    },[location])

    return analytics
}
