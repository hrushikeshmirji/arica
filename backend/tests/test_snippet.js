async (page) => {
  await page.goto('http://localhost:8443/dashboard');
  return { success: true, title: await page.title() };
}
