// Components index - Export all components

// Core UI Components (In Use)
export { default as Navigation } from './Navigation';
export { default as LoadingSpinner, SkeletonCard, SkeletonList, LoadingButton } from './LoadingSpinner';
export { default as ErrorBoundary, ErrorMessage, EmptyState } from './ErrorBoundary';
export { ToastProvider, useToast, Toast } from './Toast';

// Tutor Components (In Use)
export { default as TutorMessage } from './TutorMessage';
export { default as QuestionForm } from './QuestionForm';
export { default as FeedbackCard } from './FeedbackCard';
export { default as HintButtons } from './HintButtons';

// Analytics Components (In Use)
export { default as MasteryChart } from './MasteryChart';
export { default as TimelineChart } from './TimelineChart';

// Legacy Components (Available for future use)
// These were part of earlier designs and can be re-integrated

// Landing page variants
export { default as LandingHero } from './LandingHero';
export { default as FeatureCard } from './FeatureCard';
export { default as HowItWorks } from './HowItWorks';
export { default as Footer } from './Footer';

// Dashboard variants
export { default as DashboardMetrics } from './DashboardMetrics';
export { default as LearningPathCard } from './LearningPathCard';
export { default as ProgressCard } from './ProgressCard';
