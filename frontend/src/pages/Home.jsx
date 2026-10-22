import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <section className="hero">
      <p className="eyebrow">For small business owners</p>
      <h1 className="display">Is your business making money?</h1>
      <p className="lede">
        Answer three short questions about your costs, prices and sales. You’ll get a clear status,
        how many more sales you need to break even, and one thing to do next.
      </p>
      <Link to="/new" className="btn btn-primary btn-block">Start — takes 2 minutes</Link>
      <Link to="/new?example=1" className="btn btn-ghost btn-block">
        Try it with sample numbers
      </Link>
      <ul className="facts">
        <li><strong>No sign-up.</strong> You get a private link to come back to.</li>
        <li><strong>Plain numbers.</strong> Everything is per month, in dollars.</li>
      </ul>
    </section>
  )
}
