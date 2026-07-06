import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowRight,
  Cpu,
  FileScan,
  Gauge,
  Layers,
  Moon,
  ScanText,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  Zap,
} from 'lucide-react'
import { Logo } from '@/components/layout/Logo'
import { ThemeToggle } from '@/components/layout/ThemeToggle'
import { Button } from '@/components/ui/Button'
import { GradientBlobs } from '@/components/common/GradientBlobs'
import { PageTransition } from '@/components/common/PageTransition'
import { staggerContainer, staggerItem } from '@/components/common/PageTransition'

const FEATURES = [
  {
    icon: ScanText,
    title: 'CRNN + Transformer models',
    description: 'Character-level CRNN and word/line-level TrOCR recognition, side by side.',
  },
  {
    icon: UploadCloud,
    title: 'Images & PDFs',
    description: 'Drag and drop handwritten photos or scanned PDF pages — first page rendered automatically.',
  },
  {
    icon: Gauge,
    title: 'Confidence scoring',
    description: 'Every recognition returns a calibrated confidence score so you know what to double-check.',
  },
  {
    icon: ShieldCheck,
    title: 'Private by design',
    description: 'Runs against your own OCR backend — your documents never leave your infrastructure.',
  },
]

const STEPS = [
  { icon: UploadCloud, title: 'Upload', description: 'Drop a handwritten Nepali image or PDF page.' },
  { icon: Cpu, title: 'Recognize', description: 'Pick a model and let the AI read the handwriting.' },
  { icon: FileScan, title: 'Export', description: 'Copy the Unicode text or download as TXT / PDF.' },
]

const BADGES = [
  { icon: Sparkles, label: 'Modern & Beautiful UI' },
  { icon: Moon, label: 'Dark & Light Mode' },
  { icon: Cpu, label: 'AI Powered' },
  { icon: Layers, label: 'Fully Responsive' },
  { icon: Zap, label: 'Smooth Animations' },
  { icon: ShieldCheck, label: 'Premium Experience' },
]

export default function LandingPage() {
  return (
    <PageTransition>
      <div className="min-h-screen bg-surface-light dark:bg-surface-dark">
        <header className="sticky top-0 z-40 border-b border-slate-200/60 bg-white/70 backdrop-blur-xl dark:border-white/10 dark:bg-surface-dark/70">
          <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
            <Logo />
            <div className="flex items-center gap-2 sm:gap-3">
              <ThemeToggle />
              <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
                <Link to="/login">Sign in</Link>
              </Button>
              <Button asChild size="sm">
                <Link to="/signup">
                  Get Started <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </Button>
            </div>
          </div>
        </header>

        <section className="relative overflow-hidden px-4 pb-20 pt-16 sm:px-6 sm:pt-24">
          <GradientBlobs />
          <div className="relative z-10 mx-auto max-w-3xl text-center">
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-4 py-1.5 text-xs font-semibold text-violet-700 dark:border-violet-500/20 dark:bg-violet-500/10 dark:text-violet-300"
            >
              <Sparkles className="h-3.5 w-3.5" /> AI-Powered Devanagari Recognition
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white sm:text-6xl"
            >
              Turn handwritten Nepali <span className="text-gradient-brand">into Unicode text</span> in seconds
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="mx-auto mt-5 max-w-xl text-base text-slate-500 dark:text-slate-400"
            >
              Upload a handwritten Devanagari image or PDF, choose a recognition model, and get accurate,
              editable text with a confidence score — powered by a real trained CRNN + Transformer pipeline.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="mt-8 flex flex-wrap items-center justify-center gap-3"
            >
              <Button asChild size="lg">
                <Link to="/signup">
                  Start Recognizing <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link to="/login">Sign in to your account</Link>
              </Button>
            </motion.div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: '-80px' }}
            className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4"
          >
            {FEATURES.map((f) => (
              <motion.div
                key={f.title}
                variants={staggerItem}
                className="card-surface group p-5 transition-all duration-300 hover:-translate-y-1 hover:shadow-glow"
              >
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-brand-soft text-violet-600 transition-transform duration-300 group-hover:scale-110 dark:text-violet-400">
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{f.title}</h3>
                <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">{f.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </section>

        <section className="bg-slate-50/70 px-4 py-16 dark:bg-white/[0.02] sm:px-6">
          <div className="mx-auto max-w-4xl">
            <div className="mb-10 text-center">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">How it works</h2>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Three steps from handwriting to text</p>
            </div>
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: '-80px' }}
              className="grid grid-cols-1 gap-6 sm:grid-cols-3"
            >
              {STEPS.map((step, i) => (
                <motion.div key={step.title} variants={staggerItem} className="relative text-center">
                  <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-brand text-white shadow-glow">
                    <step.icon className="h-6 w-6" />
                  </div>
                  <p className="text-xs font-semibold text-violet-500">Step {i + 1}</p>
                  <h3 className="mt-1 text-base font-semibold text-slate-900 dark:text-white">{step.title}</h3>
                  <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">{step.description}</p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
          <div className="flex flex-wrap items-center justify-center gap-3">
            {BADGES.map((b) => (
              <span
                key={b.label}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-600 shadow-soft dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300"
              >
                <b.icon className="h-3.5 w-3.5 text-violet-500 dark:text-violet-400" />
                {b.label}
              </span>
            ))}
          </div>
        </section>

        <section className="px-4 pb-20 sm:px-6">
          <div className="relative mx-auto max-w-4xl overflow-hidden rounded-3xl bg-gradient-brand p-10 text-center text-white shadow-glow sm:p-14">
            <GradientBlobs className="opacity-40" />
            <div className="relative z-10">
              <h2 className="text-2xl font-bold sm:text-3xl">Ready to digitize your handwritten Nepali documents?</h2>
              <p className="mx-auto mt-3 max-w-md text-sm text-white/80">
                Create a free account and run your first recognition in under a minute.
              </p>
              <Button asChild size="lg" variant="secondary" className="mt-6 bg-white text-violet-700 hover:bg-white/90">
                <Link to="/signup">
                  Create Free Account <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </section>

        <footer className="border-t border-slate-200 px-4 py-6 text-center text-xs text-slate-400 dark:border-white/10 sm:px-6">
          © {new Date().getFullYear()} Devanagari OCR · Final year project · Built for research &amp; education
        </footer>
      </div>
    </PageTransition>
  )
}
