import { http, HttpResponse } from "msw"
import { server } from "@/mocks/server"
import { get, post, ApiError } from "./client"

describe("API client", () => {
  describe("get()", () => {
    it("returns parsed JSON on success", async () => {
      server.use(
        http.get("/test-path", () => HttpResponse.json({ value: 42 })),
      )
      const result = await get<{ value: number }>("/test-path")
      expect(result).toEqual({ value: 42 })
    })

    it("throws ApiError with status and message on HTTP error", async () => {
      server.use(
        http.get("/test-path", () =>
          HttpResponse.json(
            { error: "Not found", detail: "Resource missing" },
            { status: 404 },
          ),
        ),
      )
      try {
        await get("/test-path")
        expect.fail("should have thrown")
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError)
        const err = e as ApiError
        expect(err.status).toBe(404)
        expect(err.message).toBe("Resource missing")
      }
    })

    it("throws ApiError with statusText when body is not JSON", async () => {
      server.use(
        http.get("/test-path", () =>
          new HttpResponse("Internal Server Error", {
            status: 500,
            statusText: "Internal Server Error",
          }),
        ),
      )
      try {
        await get("/test-path")
        expect.fail("should have thrown")
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError)
        const err = e as ApiError
        expect(err.status).toBe(500)
        expect(err.message).toBe("Internal Server Error")
      }
    })
  })

  describe("post()", () => {
    it("sends JSON body and returns response", async () => {
      server.use(
        http.post("/test-path", async ({ request }) => {
          const body = await request.json()
          return HttpResponse.json({ received: body })
        }),
      )
      const result = await post<{ received: unknown }>("/test-path", {
        key: "value",
      })
      expect(result).toEqual({ received: { key: "value" } })
    })
  })

  describe("error formatting", () => {
    it("formats validation error detail array", async () => {
      server.use(
        http.post("/test-path", () =>
          HttpResponse.json(
            {
              error: "Validation Error",
              detail: [
                { type: "missing", loc: ["body", "code"], msg: "Field required", input: null },
                { type: "missing", loc: ["body", "display"], msg: "Field required", input: null },
              ],
            },
            { status: 422 },
          ),
        ),
      )
      try {
        await post("/test-path", {})
        expect.fail("should have thrown")
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError)
        const err = e as ApiError
        expect(err.message).toBe(
          "body.code: Field required; body.display: Field required",
        )
      }
    })

    it("uses error field when detail is missing", async () => {
      server.use(
        http.get("/test-path", () =>
          HttpResponse.json(
            { error: "Something went wrong" },
            { status: 500 },
          ),
        ),
      )
      try {
        await get("/test-path")
        expect.fail("should have thrown")
      } catch (e) {
        expect(e).toBeInstanceOf(ApiError)
        const err = e as ApiError
        expect(err.message).toBe("Something went wrong")
      }
    })
  })
})
