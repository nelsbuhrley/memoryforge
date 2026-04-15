const variants = {
  primary: 'bg-forge-600 hover:bg-forge-700 text-white',
  secondary: 'bg-slate-700 hover:bg-slate-600 text-white',
  ghost: 'bg-transparent hover:bg-slate-800 text-slate-300',
  danger: 'bg-red-600 hover:bg-red-700 text-white',
}

const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  type = 'button',
  className = '',
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`
        inline-flex items-center justify-center gap-2 rounded-lg font-medium
        transition-colors focus:outline-none focus:ring-2 focus:ring-forge-500 focus:ring-offset-2
        focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed
        ${variants[variant]} ${sizes[size]} ${className}
      `}
    >
      {children}
    </button>
  )
}
