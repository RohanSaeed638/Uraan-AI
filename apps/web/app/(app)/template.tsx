/** Every page of the app eases in: a short fade and a few pixels of rise. A template (unlike a layout)
 * starts again on each navigation. It is plain CSS (see `.page-in` in globals.css) so the server and the
 * browser always render the same markup; people who ask for less motion get an instant page from the
 * reduced-motion rule there. */
export default function Template({ children }: { children: React.ReactNode }) {
  return <div className="page-in">{children}</div>;
}
